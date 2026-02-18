import { apiClient } from '../api-client';

// ============================================================================
// Types
// ============================================================================

export enum KYCStatus {
    NOT_STARTED = "not_started",
    IN_PROGRESS = "in_progress",
    PENDING_REVIEW = "pending_review",
    VERIFIED = "verified",
    REJECTED = "rejected"
}

export interface KYCData {
    first_name: string;
    last_name: string;
    date_of_birth: string; // YYYY-MM-DD
    nationality: string; // ISO CC
    phone_number: string;
    street_address: string;
    city: string;
    postal_code: string;
    country: string; // ISO CC
    id_type: 'passport' | 'drivers_license' | 'national_id';
    id_number: string;
    occupation: string;
    employment_status: 'employed' | 'self_employed' | 'unemployed' | 'retired' | 'student';
    annual_income: '0-25k' | '25k-50k' | '50k-100k' | '100k-250k' | '250k+';
    source_of_funds: string;
}

export interface KYCResponse {
    status: KYCStatus;
    submitted_at?: string;
    reviewed_at?: string;
    rejection_reason?: string;
    required: boolean;
    enabled: boolean;
}

export interface KYCSubmitResponse {
    success: boolean;
    message: string;
    status: KYCStatus;
}

// ============================================================================
// KYC API
// ============================================================================

export const kycApi = {
    /**
     * Get current KYC status
     */
    getStatus: async (): Promise<KYCResponse> => {
        const response = await apiClient.get<KYCResponse>('/api/v1/kyc/status');
        return response.data;
    },

    /**
     * Submit KYC data
     */
    submit: async (data: KYCData): Promise<KYCSubmitResponse> => {
        const response = await apiClient.post<KYCSubmitResponse>('/api/v1/kyc/submit', data);
        return response.data;
    },

    /**
     * Upload KYC documents
     */
    uploadDocuments: async (files: { id_front?: File, id_back?: File, selfie?: File }): Promise<any> => {
        const formData = new FormData();
        if (files.id_front) formData.append('id_front', files.id_front);
        if (files.id_back) formData.append('id_back', files.id_back);
        if (files.selfie) formData.append('selfie', files.selfie);

        const response = await apiClient.post('/api/v1/kyc/documents', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Check if KYC is required
     */
    isRequired: async (): Promise<{ required: boolean; enabled: boolean; status: KYCStatus }> => {
        const response = await apiClient.get<any>('/api/v1/kyc/required');
        return response.data;
    }
};
