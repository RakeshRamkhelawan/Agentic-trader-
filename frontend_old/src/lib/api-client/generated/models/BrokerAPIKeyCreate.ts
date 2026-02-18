/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExchangeType } from './ExchangeType';
/**
 * Request to add new broker API key.
 */
export type BrokerAPIKeyCreate = {
    exchange: ExchangeType;
    /**
     * Exchange API key
     */
    api_key: string;
    /**
     * Exchange API secret
     */
    api_secret: string;
    /**
     * Optional passphrase (for Coinbase)
     */
    passphrase?: (string | null);
};

