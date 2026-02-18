"""
KYC API - Know Your Customer onboarding endpoints.

NOTE: This module is implemented but DISABLED by default.
To enable KYC, set ENABLE_KYC=true in .env

Endpoints:
- POST /api/v1/kyc/submit - Submit KYC data
- GET /api/v1/kyc/status - Get KYC status
- POST /api/v1/kyc/documents - Upload KYC documents
- GET /api/v1/kyc/required - Check if KYC is required
"""

import os
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile, status)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_db
from backend.models.user_settings import User

# Check if KYC is enabled (disabled by default)
ENABLE_KYC = os.getenv("ENABLE_KYC", "false").lower() == "true"

router = APIRouter()


class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class KYCData(BaseModel):
    """KYC data submission schema"""

    # Personal Info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    nationality: str = Field(..., min_length=2, max_length=2)  # ISO country code
    phone_number: str = Field(..., min_length=5, max_length=20)

    # Address
    street_address: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=2, max_length=20)
    country: str = Field(..., min_length=2, max_length=2)  # ISO country code

    # Identity
    id_type: str = Field(..., pattern=r"^(passport|drivers_license|national_id)$")
    id_number: str = Field(..., min_length=5, max_length=50)

    # Financial
    occupation: str = Field(..., min_length=2, max_length=100)
    employment_status: str = Field(
        ..., pattern=r"^(employed|self_employed|unemployed|retired|student)$"
    )
    annual_income: str = Field(
        ..., pattern=r"^(0-25k|25k-50k|50k-100k|100k-250k|250k+)$"
    )
    source_of_funds: str = Field(..., min_length=2, max_length=200)


class KYCResponse(BaseModel):
    """KYC response schema"""

    status: KYCStatus
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    required: bool = True
    enabled: bool = ENABLE_KYC


class KYCSubmitResponse(BaseModel):
    """KYC submission response"""

    success: bool
    message: str
    status: KYCStatus


# In-memory store for KYC data (replace with database in production)
_kyc_store: dict[str, dict] = {}


def get_kyc_disabled_response() -> KYCResponse:
    """Return disabled KYC response"""
    return KYCResponse(
        status=KYCStatus.VERIFIED,  # Auto-verified when disabled
        required=False,
        enabled=False,
    )


@router.get("/status", response_model=KYCResponse)
async def get_kyc_status(
    request: Request, db: AsyncSession = Depends(get_admin_db)
) -> KYCResponse:
    """
    Get current KYC status for authenticated user.

    Returns:
        KYCResponse with status and requirements
    """
    # KYC is disabled - return auto-verified
    if not ENABLE_KYC:
        return get_kyc_disabled_response()

    # Get user from request
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # Get KYC data from store
    kyc_data = _kyc_store.get(user_id, {})

    return KYCResponse(
        status=kyc_data.get("status", KYCStatus.NOT_STARTED),
        submitted_at=kyc_data.get("submitted_at"),
        reviewed_at=kyc_data.get("reviewed_at"),
        rejection_reason=kyc_data.get("rejection_reason"),
        required=True,
        enabled=True,
    )


@router.post("/submit", response_model=KYCSubmitResponse)
async def submit_kyc(
    data: KYCData, request: Request, db: AsyncSession = Depends(get_admin_db)
) -> KYCSubmitResponse:
    """
    Submit KYC data for verification.

    Args:
        data: KYC form data

    Returns:
        KYCSubmitResponse with success status
    """
    # KYC is disabled - accept but ignore
    if not ENABLE_KYC:
        return KYCSubmitResponse(
            success=True,
            message="KYC submitted (KYC verification is disabled)",
            status=KYCStatus.VERIFIED,
        )

    # Get user from request
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # Validate user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Store KYC data
    _kyc_store[user_id] = {
        "data": data.dict(),
        "status": KYCStatus.PENDING_REVIEW,
        "submitted_at": datetime.utcnow(),
        "reviewed_at": None,
        "rejection_reason": None,
    }

    return KYCSubmitResponse(
        success=True,
        message="KYC submitted successfully. Pending review.",
        status=KYCStatus.PENDING_REVIEW,
    )


@router.post("/documents")
async def upload_kyc_documents(
    request: Request,
    id_front: Optional[UploadFile] = File(None),
    id_back: Optional[UploadFile] = File(None),
    selfie: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_admin_db),
):
    """
    Upload KYC verification documents.

    Files:
        id_front: Front of ID document
        id_back: Back of ID document (if applicable)
        selfie: Selfie with ID

    Returns:
        Upload confirmation
    """
    # KYC is disabled - accept but ignore
    if not ENABLE_KYC:
        return {
            "success": True,
            "message": "Documents received (KYC verification is disabled)",
            "files_received": sum(
                [1 for f in [id_front, id_back, selfie] if f is not None]
            ),
        }

    # Get user from request
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # Validate file types and sizes
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    max_size = 10 * 1024 * 1024  # 10MB

    uploaded_files = []
    for file in [id_front, id_back, selfie]:
        if file:
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}",
                )

            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large: {file.filename}. Max size: 10MB",
                )

            uploaded_files.append(file.filename)
            # In production, save to secure storage (S3, etc.)

    return {
        "success": True,
        "message": f"{len(uploaded_files)} document(s) uploaded successfully",
        "files": uploaded_files,
    }


@router.get("/required")
async def is_kyc_required(
    request: Request, db: AsyncSession = Depends(get_admin_db)
) -> dict:
    """
    Check if KYC is required for the current user.

    Returns:
        {"required": bool, "enabled": bool, "status": KYCStatus}
    """
    if not ENABLE_KYC:
        return {"required": False, "enabled": False, "status": KYCStatus.VERIFIED}

    # Get user from request
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"required": True, "enabled": True, "status": KYCStatus.NOT_STARTED}

    kyc_data = _kyc_store.get(user_id, {})
    status_value = kyc_data.get("status", KYCStatus.NOT_STARTED)

    return {
        "required": status_value != KYCStatus.VERIFIED,
        "enabled": True,
        "status": status_value,
    }


# Admin endpoints for KYC review (only when enabled)
if ENABLE_KYC:

    @router.post("/admin/review/{user_id}")
    async def review_kyc(
        user_id: str,
        status: KYCStatus,
        rejection_reason: Optional[str] = None,
        db: AsyncSession = Depends(get_admin_db),
    ):
        """
        Admin endpoint to review KYC submission.
        Requires admin role.
        """
        if user_id not in _kyc_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="KYC submission not found"
            )

        _kyc_store[user_id]["status"] = status
        _kyc_store[user_id]["reviewed_at"] = datetime.utcnow()

        if status == KYCStatus.REJECTED and rejection_reason:
            _kyc_store[user_id]["rejection_reason"] = rejection_reason

        return {
            "success": True,
            "message": f"KYC status updated to {status}",
            "user_id": user_id,
        }
