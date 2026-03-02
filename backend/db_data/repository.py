"""
Standardized Data Access Layer using Repository Pattern.

Provides a consistent interface for database interactions with:
- Automatic RLS context management via SessionManager
- Standardized CRUD operations
- Type-safe async methods
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import Base

# Define generic type for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base Repository with default CRUD operations.
    Enforces RLS via SessionManager.tenant_session() or system_admin_session().
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository for a specific SQLAlchemy model.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        """
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        descending: bool = True,
    ) -> List[ModelType]:
        """
        Get all records with pagination and sorting.
        """
        query = select(self.model)

        # Apply sorting if field exists
        if hasattr(self.model, sort_by):
            order_col = getattr(self.model, sort_by)
            query = query.order_by(desc(order_col) if descending else asc(order_col))

        result = await session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create(
        self, session: AsyncSession, obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Create a new record.
        """
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)

        db_obj = self.model(**create_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update an existing record.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Update model attributes
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Delete a record by ID.
        """
        obj = await self.get(session, id)
        if obj:
            await session.delete(obj)
            await session.commit()
        return obj

    async def count(self, session: AsyncSession) -> int:
        """
        Count total records.
        """
        query = select(func.count()).select_from(self.model)
        result = await session.execute(query)
        return result.scalar()
