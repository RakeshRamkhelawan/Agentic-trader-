# Bitvavo Exchange Setup Guide

## Overview

Bitvavo is a Dutch cryptocurrency exchange that's ideal for European traders:
- ✅ EUR trading pairs (BTC-EUR, ETH-EUR, etc.)
- ✅ iDEAL/Bancontact deposits
- ✅ Dutch regulatory compliance (DNB registered)
- ✅ Competitive fees (0.15% maker, 0.25% taker)
- ✅ User-friendly API

## Setup Instructions

### 1. Create Bitvavo Account

1. Go to https://bitvavo.com
2. Sign up and complete KYC verification
3. Deposit EUR via iDEAL, Bancontact, or SEPA

### 2. Generate API Keys

1. Log in to your Bitvavo account
2. Go to: https://account.bitvavo.com/user/api-keys
3. Click "Create API Key"
4. Give it a name (e.g., "Agentic Trader")
5. **IMPORTANT**: Enable these permissions:
   - ✅ View data
   - ✅ Buy/Sell assets
   - ❌ Withdraw funds (keep disabled for security)
6. Copy the **API Key** and **API Secret**

### 3. Configure .env File

Add these lines to your `.env` file:

```bash
# Bitvavo API Credentials
BITVAVO_API_KEY="your_api_key_here"
BITVAVO_API_SECRET="your_api_secret_here"
BITVAVO_SANDBOX=false
```

**Replace** `your_api_key_here` and `your_api_secret_here` with the actual values from Bitvavo.

### 4. Test the Connection

Run the test script:

```bash
python scripts/test_bitvavo_connection.py
```

You should see:
- ✅ Account balance (EUR and crypto)
- ✅ Current BTC/EUR price
- ✅ Order book data
- ✅ List of available EUR pairs

### 5. Set as Active Exchange

To use Bitvavo as your active exchange, set in `.env`:

```bash
EXCHANGE_ID=bitvavo
```

## Available Trading Pairs

Bitvavo offers 200+ EUR trading pairs including:

| Pair | Description |
|------|-------------|
| BTC/EUR | Bitcoin |
| ETH/EUR | Ethereum |
| SOL/EUR | Solana |
| ADA/EUR | Cardano |
| XRP/EUR | Ripple |
| DOT/EUR | Polkadot |
| LINK/EUR | Chainlink |
| MATIC/EUR | Polygon |

View all pairs: `python -c "from backend.execution.bitvavo_adapter import BitvavoAdapter; import asyncio; b = BitvavoAdapter(); asyncio.run(b.initialize()); print(b.get_eur_pairs())"`

## Trading Configuration

### Minimum Order Sizes

Bitvavo has minimum order sizes:
- BTC: €5 minimum
- ETH: €5 minimum
- Other crypto: €5 minimum

### Fees

| Type | Fee |
|------|-----|
| Market Buy (Taker) | 0.25% |
| Limit Buy (Maker) | 0.15% |
| Market Sell (Taker) | 0.25% |
| Limit Sell (Maker) | 0.15% |

Lower fees apply for higher monthly volumes.

## Risk Management

### Recommended Settings for Bitvavo

Add to your `.env`:

```bash
# Conservative limits for EUR trading
MAX_ORDER_SIZE_EUR=500.0        # Max €500 per trade
MAX_DAILY_LOSS_EUR=100.0        # Max €100 loss per day
TRADING_MODE=paper              # Start with paper trading!
```

### Paper Trading (Testing)

To test without real money:
1. Keep `TRADING_MODE=paper` in `.env`
2. The system will simulate trades
3. Monitor performance before going live

## Troubleshooting

### "API credentials not configured"

**Solution**: Check your `.env` file has:
```bash
BITVAVO_API_KEY="your_actual_key"
BITVAVO_API_SECRET="your_actual_secret"
```

### "Invalid API key"

**Solution**:
1. Regenerate API keys at https://account.bitvavo.com/user/api-keys
2. Ensure you're copying both key AND secret
3. Check for extra spaces or quotes

### "Insufficient balance"

**Solution**:
1. Deposit EUR to your Bitvavo account
2. Check `TRADING_MODE=paper` if testing

### Rate Limiting

Bitvavo API limits:
- 1000 requests per minute for most endpoints
- The system has built-in rate limiting

## Security Best Practices

1. **Never share API keys**
2. **Disable withdrawal permissions** on API keys
3. **Use IP whitelist** if possible (Bitvavo Pro feature)
4. **Store .env file securely** (never commit to git)
5. **Start with small amounts** when going live

## Switching Between Exchanges

To switch to another exchange, change `EXCHANGE_ID`:

```bash
# For Bitvavo (EUR pairs)
EXCHANGE_ID=bitvavo

# For Kraken
EXCHANGE_ID=kraken

# For Binance
EXCHANGE_ID=binance
```

## Next Steps

1. ✅ API keys configured
2. ✅ Connection tested
3. ⏭️ Start paper trading
4. ⏭️ Monitor Unified Consciousness Dashboard
5. ⏭️ Go live with small amounts

## Support

- Bitvavo Help: https://support.bitvavo.com
- Bitvavo API Docs: https://docs.bitvavo.com/
- System Issues: Check logs in `backend/logs/`
