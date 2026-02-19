# Asset Fetcher Scripts

Scripts to fetch and export trading assets from cryptocurrency exchanges.

## Scripts

### 1. `fetch_bitvavo_assets.py`

Fetches all trading pairs from Bitvavo exchange using CCXT.

**Requirements:**
```bash
pip install ccxt
```

**Usage:**
```bash
python scripts/fetch_bitvavo_assets.py
```

**Output:**
- `data/bitvavo_assets.csv` - All trading pairs with details
- `data/bitvavo_assets.json` - JSON version
- `data/bitvavo_unique_assets.csv` - Unique base assets only
- `data/bitvavo_unique_assets.json` - JSON version

**Columns:**
- `symbol` - Trading pair (e.g., "BTC-EUR")
- `baseAsset` - Base currency (e.g., "BTC")
- `quoteAsset` - Quote currency (e.g., "EUR")
- `status` - active/inactive
- `type` - spot/future/etc
- `precision_price` - Price precision
- `precision_amount` - Amount precision
- `limits_min` - Minimum order size
- `limits_max` - Maximum order size

---

### 2. `fetch_revolut_assets.py`

Fetches assets from Revolut X. Note: Revolut X doesn't have a public API like Bitvavo.

**Requirements:**
```bash
pip install httpx
```

**Usage:**
```bash
python scripts/fetch_revolut_assets.py
```

**Output:**
- `data/revolutx_assets.csv` - Trading pairs
- `data/revolutx_assets.json` - JSON version
- `data/revolutx_unique_assets.csv` - Unique base assets
- `data/revolutx_unique_assets.json` - JSON version

**Method:**
1. Tries CCXT first (if Revolut is supported)
2. Tries direct API call to Revolut endpoints
3. Falls back to manual asset list (10 major pairs)

**For Complete Asset List via Browser Dev Tools:**

1. Open Revolut X in your browser (https://revolut.com/crypto)
2. Log in and navigate to the trading interface
3. Open Developer Tools (F12)
4. Go to Network tab
5. Look for API calls like:
   - `token-list`
   - `markets`
   - `instruments`
6. Copy the JSON response
7. Save to `data/revolutx_manual.json`
8. Run the script again to process the manual file

---

## Sample Output

### Bitvavo (448 markets, 437 unique assets)
```csv
symbol,baseAsset,quoteAsset,status,type,precision_price,precision_amount,limits_min,limits_max
BTC-EUR,BTC,EUR,active,spot,0.01,0.00000001,0.0001,1000
ETH-EUR,ETH,EUR,active,spot,0.01,0.00000001,0.001,10000
...
```

### Revolut X (10 fallback assets)
```csv
symbol,baseAsset,quoteAsset,name,status
BTC-EUR,BTC,EUR,Bitcoin,active
ETH-EUR,ETH,EUR,Ethereum,active
...
```

---

## Notes

- **Bitvavo**: Uses public API, no authentication required for market data
- **Revolut X**: No public API; uses fallback list or manual extraction
- Both scripts create the `data/` directory if it doesn't exist
- CSV files use UTF-8 encoding
