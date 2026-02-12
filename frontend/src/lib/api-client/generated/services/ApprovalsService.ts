/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ApprovalsService {
    /**
     * Get Pending Approvals
     * List all orders waiting for approval.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPendingApprovalsApiV1ApprovalsPendingGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/approvals/pending',
        });
    }
    /**
     * Approve Order
     * Approve a pending order. Forces execution.
     * @param orderId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static approveOrderApiV1ApprovalsOrderIdApprovePost(
        orderId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/approvals/{order_id}/approve',
            path: {
                'order_id': orderId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reject Order
     * Reject a pending order.
     * @param orderId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rejectOrderApiV1ApprovalsOrderIdRejectPost(
        orderId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/approvals/{order_id}/reject',
            path: {
                'order_id': orderId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
