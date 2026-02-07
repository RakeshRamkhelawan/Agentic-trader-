/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AppearanceSettings } from '../models/AppearanceSettings';
import type { BrokerAPIKey } from '../models/BrokerAPIKey';
import type { BrokerAPIKeyCreate } from '../models/BrokerAPIKeyCreate';
import type { NotificationSettings } from '../models/NotificationSettings';
import type { SecuritySettings } from '../models/SecuritySettings';
import type { UserPreferences } from '../models/UserPreferences';
import type { UserProfile } from '../models/UserProfile';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SettingsService {
    /**
     * Get Profile
     * @returns UserProfile Successful Response
     * @throws ApiError
     */
    public static getProfileApiV1SettingsProfileGet(): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/profile',
        });
    }
    /**
     * Update Profile
     * @param requestBody
     * @returns UserProfile Successful Response
     * @throws ApiError
     */
    public static updateProfileApiV1SettingsProfilePut(
        requestBody: UserProfile,
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/settings/profile',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Notifications
     * @returns NotificationSettings Successful Response
     * @throws ApiError
     */
    public static getNotificationsApiV1SettingsNotificationsGet(): CancelablePromise<NotificationSettings> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/notifications',
        });
    }
    /**
     * Update Notifications
     * @param requestBody
     * @returns NotificationSettings Successful Response
     * @throws ApiError
     */
    public static updateNotificationsApiV1SettingsNotificationsPut(
        requestBody: NotificationSettings,
    ): CancelablePromise<NotificationSettings> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/settings/notifications',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Security Settings
     * @returns SecuritySettings Successful Response
     * @throws ApiError
     */
    public static getSecuritySettingsApiV1SettingsSecurityGet(): CancelablePromise<SecuritySettings> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/security',
        });
    }
    /**
     * Toggle 2Fa
     * @param enabled
     * @returns any Successful Response
     * @throws ApiError
     */
    public static toggle2FaApiV1SettingsSecurity2FaPost(
        enabled: boolean,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/settings/security/2fa',
            query: {
                'enabled': enabled,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Change Password
     * @param currentPassword
     * @param newPassword
     * @returns any Successful Response
     * @throws ApiError
     */
    public static changePasswordApiV1SettingsSecurityPasswordPost(
        currentPassword: string,
        newPassword: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/settings/security/password',
            query: {
                'current_password': currentPassword,
                'new_password': newPassword,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Appearance
     * @returns AppearanceSettings Successful Response
     * @throws ApiError
     */
    public static getAppearanceApiV1SettingsAppearanceGet(): CancelablePromise<AppearanceSettings> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/appearance',
        });
    }
    /**
     * Update Appearance
     * @param requestBody
     * @returns AppearanceSettings Successful Response
     * @throws ApiError
     */
    public static updateAppearanceApiV1SettingsAppearancePut(
        requestBody: AppearanceSettings,
    ): CancelablePromise<AppearanceSettings> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/settings/appearance',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Api Keys
     * @returns BrokerAPIKey Successful Response
     * @throws ApiError
     */
    public static getApiKeysApiV1SettingsApiKeysGet(): CancelablePromise<Array<BrokerAPIKey>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/api-keys',
        });
    }
    /**
     * Add Api Key
     * @param requestBody
     * @returns BrokerAPIKey Successful Response
     * @throws ApiError
     */
    public static addApiKeyApiV1SettingsApiKeysPost(
        requestBody: BrokerAPIKeyCreate,
    ): CancelablePromise<BrokerAPIKey> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/settings/api-keys',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Api Key
     * @param keyId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteApiKeyApiV1SettingsApiKeysKeyIdDelete(
        keyId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/settings/api-keys/{key_id}',
            path: {
                'key_id': keyId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Preferences
     * @returns UserPreferences Successful Response
     * @throws ApiError
     */
    public static getPreferencesApiV1SettingsPreferencesGet(): CancelablePromise<UserPreferences> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/preferences',
        });
    }
    /**
     * Update Preferences
     * @param requestBody
     * @returns UserPreferences Successful Response
     * @throws ApiError
     */
    public static updatePreferencesApiV1SettingsPreferencesPut(
        requestBody: UserPreferences,
    ): CancelablePromise<UserPreferences> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/settings/preferences',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get All Settings
     * Aggregate all settings for initial load.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAllSettingsApiV1SettingsAllGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings/all',
        });
    }
}
