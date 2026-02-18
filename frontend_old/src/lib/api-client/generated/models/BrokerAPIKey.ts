/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExchangeType } from './ExchangeType';
/**
 * Broker API key (response model - key is masked).
 */
export type BrokerAPIKey = {
    id: string;
    exchange: ExchangeType;
    /**
     * Masked API key (last 4 chars visible)
     */
    api_key_masked: string;
    created_at: string;
    last_used?: (string | null);
    is_valid?: boolean;
};

