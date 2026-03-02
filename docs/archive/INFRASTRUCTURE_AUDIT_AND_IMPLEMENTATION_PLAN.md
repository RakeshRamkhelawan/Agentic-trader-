# Infrastructure Audit & Realistic Implementation Plan

**Date:** 2025-01-18
**Auditor:** Code Analysis
**Status:** READY FOR IMPLEMENTATION

---

## 1. Executive Summary

De huidige infrastructuur is **productie-ready** en kan de volledige 448-asset implementatie ondersteunen met minimale wijzigingen. Dit audit rapport bevestigt dat alle benodigde componenten aanwezig zijn, en presenteert een realistisch implementatieplan dat aansluit bij de bestaande architectuur.

### Key Finding: ✅ INFRASTRUCTURE READY
- PostgreSQL (TimescaleDB): ✅ Ready for asset registry
- Redis: ✅ Ready for tiered caching
- Redpanda (Kafka): ✅ Ready for event streaming
- ClickHouse: ✅ Ready for analytics
- API Server: ✅ Ready for asset endpoints
- Frontend: ✅ Ready for asset selector

---

## 2. Infrastructure Audit

### 2.1 Current Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRENT INFRASTRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    DATABASE LAYER (PostgreSQL + TimescaleDB)            ││
│  │  ✅ Max connections: 200                                                ││
│  │  ✅ Shared buffers: 256MB                                               ││
│  │  ✅ Current tables: users, orders, market_data, decision_logs           ││
│  │  ⚠️  MISSING: asset_registry, asset_categories tables                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    CACHE LAYER (Redis)                                  ││
│  │  ✅ Maxmemory: 1GB                                                      ││
│  │  ✅ Policy: allkeys-lru                                                 ││
│  │  ✅ Current keys: markets:*, tickers:*                                  ││
│  │  ✅ Connection: Async via redis.asyncio                                 ││
│  │  ✅ Class: AsyncCacheLayer (singleton pattern)                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    MESSAGE BROKER (Redpanda/Kafka)                      ││
│  │  ✅ Bootstrap: redpanda:29092                                           ││
│  │  ✅ Resources: 1-2 CPUs, 1-2GB RAM                                      ││
│  │  ✅ Console UI: Port 8081                                               ││
│  │  ⚠️  CURRENTLY UNUSED for market data (direct API calls)                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    ANALYTICS (ClickHouse)                               ││
│  │  ✅ HTTP Port: 8124                                                     ││
│  │  ✅ Native Port: 9001                                                   ││
│  │  ✅ Migrations: /backend/storage/migrations                             ││
│  │  ✅ Use case: Time-series analytics, audit logs                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    APPLICATION LAYER                                    ││
│  │                                                                          ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      ││
│  │  │  API Server      │  │  Trading Engine  │  │  Consciousness   │      ││
│  │  │  Port: 8003      │  │  Port: 8004      │  │  Port: 8006      │      ││
│  │  │  Workers: 2      │  │  CPU: 3, RAM: 4G │  │  CPU: 2, RAM: 2G │      ││
│  │  │  Status: ✅      │  │  Status: ✅      │  │  Status: ✅      │      ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘      ││
│  │                                                                          ││
│  │  ┌──────────────────┐  ┌──────────────────┐                             ││
│  │  │  Frontend        │  │  Prediction      │                             ││
│  │  │  Port: 3000      │  │  Port: 8002      │                             ││
│  │  │  Framework: Vite │  │  CPU: 2, RAM: 2G │                             ││
│  │  │  Status: ✅      │  │  Status: ✅      │                             ││
│  │  └──────────────────┘  └──────────────────┘                             ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Existing Database Schema Analysis

**Current Tables (from migrations):**
```sql
-- Core Tables (EXISTING)
✅ users, user_preferences, user_profile, user_security
✅ orders, order_status
✅ market_candles, market_ticks
✅ circuit_breaker_state
✅ decision_audit_logs
✅ trading_mode_changes
✅ agent_experience
✅ runtime_config

-- MISSING for Asset System (TO BE ADDED)
❌ assets                    -- Master asset registry
❌ asset_categories          -- Category definitions
❌ asset_exchanges           -- Exchange-specific asset data
❌ agent_asset_watchlists    -- Per-agent watched assets
❌ asset_tiers               -- Tier assignments
```

### 2.3 Current Redis Usage Analysis

**Existing Keys:**
```
markets:all           → Merged market data (10 assets)
markets:bitvavo       → Bitvavo raw data
markets:revolut       → Revolut raw data
markets:last_update   → Timestamp
instruments:{exchange} → Cached instrument lists
tickers:{source}      → Cached tickers
```

**Required New Keys:**
```
assets:all                    → Full asset registry
assets:categories             → Category mappings
assets:tier1                  → Hot assets (50)
assets:tier2                  → Warm assets (150)
assets:tier3                  → All assets (448)
assets:by_category:{cat}      → Per-category
assets:agent:{agent_id}       → Per-agent watchlist
market:tick:{symbol}          → Latest tick per asset
market:context:latest         → Full market context
```

### 2.4 Current API Structure Analysis

**Existing Endpoints (from main.py):**
```python
✅ /api/v1/health
✅ /api/v1/trading/markets        # Returns 10 assets
✅ /api/v1/trading/candles/{symbol}
✅ /api/v1/trading/orderbook/{symbol}
✅ /api/v1/agents/status
✅ /api/v1/agents/run-cycle
✅ /api/v1/portfolio/*
✅ /api/v1/orders/*

# MISSING (TO BE ADDED)
❌ /api/v1/assets                 # List all assets
❌ /api/v1/assets/categories      # Get categories
❌ /api/v1/assets/{symbol}        # Get asset detail
❌ /api/v1/assets/watch           # Add to watchlist
❌ /api/v1/market/context         # Full market context
```

### 2.5 Frontend Architecture Analysis

**Current Store (appStore.ts):**
```typescript
✅ assets: Asset[]                    # Currently 10 assets
✅ fetchAssets()                      # Loads from /trading/markets
❌ allAssets: Asset[]                 # Missing: full registry
❌ assetCategories: Category[]        # Missing: categories
❌ searchAssets(query)                # Missing: search
❌ assetsByCategory: Record<string, Asset[]>  # Missing
```

**Current Components:**
```
✅ TradingChart.tsx           # Single asset chart
✅ MarketOverview.tsx         # Simple list
✅ TopMovers.tsx              # Gainers/losers
❌ AssetSelector.tsx          # MISSING: categorized selector
❌ AssetSearch.tsx            # MISSING: search component
```

---

## 3. Gap Analysis

### 3.1 What's Missing vs. Required

| Component | Required | Current | Status |
|-----------|----------|---------|--------|
| **Database** | Asset tables | No asset tables | ❌ Need migration |
| **Redis** | Tiered keys | Basic keys | ⚠️ Need extension |
| **API** | Asset endpoints | Trading endpoints | ❌ Need routes |
| **Backend** | Tiered sync | Single tier (10s) | ⚠️ Need upgrade |
| **Frontend** | Asset selector | Basic list | ❌ Need component |
| **Agents** | Context builder | Basic signals | ⚠️ Need enhancement |

### 3.2 Resource Capacity Assessment

**Current Resource Usage:**
```
Service             CPU Limit    Memory Limit    Status
─────────────────────────────────────────────────────────
PostgreSQL          2 cores      2GB             ✅ OK
Redis               1 core       1.5GB           ✅ OK
API Server          2 cores      3GB             ✅ OK
Trading Engine      3 cores      4GB             ⚠️ Monitor
Frontend            2 cores      2GB             ✅ OK
```

**Projected Usage with 448 Assets:**
```
Component                    Additional Load    Status
────────────────────────────────────────────────────────
Database (448 assets)        +100MB             ✅ OK
Redis (tiered cache)         +200MB             ✅ OK (1.5GB limit)
API Server                   +10% CPU           ✅ OK
Market Sync (3 tiers)        +20% CPU           ✅ OK
Frontend (virtualized)       Minimal            ✅ OK
```

**Conclusion:** Current resources are sufficient for 448 assets.

---

## 4. Realistic Implementation Plan

### 4.1 Revised Architecture (Based on Existing Infra)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                 REALISTIC IMPLEMENTATION ARCHITECTURE                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    PHASE 1: DATABASE (Week 1)                            │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │  PostgreSQL (Existing)                                            │  │ │
│  │  │  ├── Migration: Add assets table                                  │  │ │
│  │  │  ├── Migration: Add asset_categories table                        │  │ │
│  │  │  ├── Migration: Add agent_asset_watchlists table                  │  │ │
│  │  │  └── Seed: Import 448 Bitvavo assets                              │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    PHASE 2: BACKEND (Week 1-2)                           │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │  MarketDataSync (ENHANCE EXISTING)                                │  │ │
│  │  │  ├── Modify: Change from 10 to 448 target symbols                 │  │ │
│  │  │  ├── Add: Tier assignment logic                                   │  │ │
│  │  │  ├── Add: Redis tiered keys (markets:tier1/2/3)                   │  │ │
│  │  │  └── Keep: Existing merge logic (Revolut + Bitvavo)               │  │ │
│  │  │                                                                  │  │ │
│  │  │  NEW: AssetRegistryService                                       │  │ │
│  │  │  ├── get_all_assets()                                            │  │ │
│  │  │  ├── get_assets_by_category()                                    │  │ │
│  │  │  ├── get_asset_detail(symbol)                                    │  │ │
│  │  │  └── update_asset_tiers()                                        │  │ │
│  │  │                                                                  │  │ │
│  │  │  NEW: AgentMarketContext (ENHANCE EXISTING)                      │  │ │
│  │  │  ├── Build context from tier1 data                               │  │ │
│  │  │  ├── Filter by agent watchlist                                   │  │ │
│  │  │  └── Send to agents via existing message_bus                     │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    PHASE 3: API (Week 2)                                 │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │  FastAPI (ENHANCE EXISTING)                                       │  │ │
│  │  │  ├── GET /api/v1/assets                                          │  │ │
│  │  │  ├── GET /api/v1/assets/categories                               │  │ │
│  │  │  ├── GET /api/v1/assets/{symbol}                                 │  │ │
│  │  │  ├── POST /api/v1/assets/{symbol}/watch                          │  │ │
│  │  │  └── GET /api/v1/market/context                                  │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    PHASE 4: FRONTEND (Week 3)                            │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Store (ENHANCE appStore.ts)                                      │  │ │
│  │  │  ├── Add: allAssets array                                        │  │ │
│  │  │  ├── Add: assetCategories                                        │  │ │
│  │  │  ├── Add: fetchAllAssets()                                       │  │ │
│  │  │  └── Add: searchAssets(query)                                    │  │ │
│  │  │                                                                  │  │ │
│  │  │  NEW COMPONENTS                                                  │  │ │
│  │  │  ├── AssetSelector.tsx (categorized dropdowns)                    │  │ │
│  │  │  ├── AssetSearch.tsx (search bar)                                │  │ │
│  │  │  └── CategoryGrid.tsx (scrollable categories)                    │  │ │
│  │  └───────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Detailed Implementation Tasks

#### Phase 1: Database (Days 1-3)

**Migration 1: Assets Table**
```python
# backend/migrations/versions/add_assets_table.py
"""
Create assets table for 448 Bitvavo assets
"""

def upgrade():
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),        # BTC-EUR
        sa.Column('base_asset', sa.String(length=10), nullable=False),    # BTC
        sa.Column('quote_asset', sa.String(length=10), nullable=False),   # EUR
        sa.Column('name', sa.String(length=100), nullable=False),         # Bitcoin
        sa.Column('category', sa.String(length=50), nullable=True),       # layer1
        sa.Column('exchange', sa.String(length=50), nullable=False),      # bitvavo
        sa.Column('tier', sa.Integer(), default=3),                       # 1, 2, 3
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('market_cap_rank', sa.Integer(), nullable=True),
        sa.Column('volume_24h', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'exchange', name='unique_asset_exchange')
    )
    op.create_index('ix_assets_symbol', 'assets', ['symbol'])
    op.create_index('ix_assets_category', 'assets', ['category'])
    op.create_index('ix_assets_tier', 'assets', ['tier'])
```

**Migration 2: Categories Table**
```python
# backend/migrations/versions/add_asset_categories.py

def upgrade():
    op.create_table(
        'asset_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),         # layer1
        sa.Column('name', sa.String(length=100), nullable=False),        # Layer 1
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=255), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # Seed categories
    op.bulk_insert('asset_categories', [
        {'slug': 'layer1', 'name': 'Layer 1', 'sort_order': 1},
        {'slug': 'defi', 'name': 'DeFi', 'sort_order': 2},
        {'slug': 'meme', 'name': 'Meme', 'sort_order': 3},
        {'slug': 'gaming', 'name': 'Gaming', 'sort_order': 4},
        {'slug': 'ai', 'name': 'AI', 'sort_order': 5},
        {'slug': 'rwa', 'name': 'Real World Assets', 'sort_order': 6},
    ])
```

**Migration 3: Agent Watchlists**
```python
# backend/migrations/versions/add_agent_watchlists.py

def upgrade():
    op.create_table(
        'agent_asset_watchlists',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.String(length=50), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), default=1),  # 1-10
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'asset_id', name='unique_agent_asset')
    )
```

**Seed Script: Import 448 Assets**
```python
# backend/scripts/seed_assets.py
"""
Import assets from data/bitvavo_assets.csv into database
"""

import csv
from backend.core.database import SessionLocal
from backend.data.models import Asset

def seed_assets():
    db = SessionLocal()

    with open('data/bitvavo_assets.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asset = Asset(
                symbol=row['symbol'],
                base_asset=row['baseAsset'],
                quote_asset=row['quoteAsset'],
                name=row['baseAsset'],  # Use base as name initially
                exchange='bitvavo',
                tier=1 if row['baseAsset'] in ['BTC', 'ETH', 'SOL'] else
                      2 if float(row.get('volume_24h', 0)) > 1000000 else 3,
                category=assign_category(row['baseAsset'])
            )
            db.add(asset)

    db.commit()
    db.close()

def assign_category(base_asset: str) -> str:
    # Simple categorization logic
    categories = {
        'layer1': ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC'],
        'defi': ['UNI', 'AAVE', 'MKR', 'COMP', 'CRV', 'SNX', 'LDO'],
        'meme': ['DOGE', 'SHIB', 'PEPE', 'FLOKI'],
        'gaming': ['SAND', 'MANA', 'AXS', 'ENJ', 'GALA'],
        'ai': ['FET', 'RNDR', 'AGIX', 'OCEAN'],
        'rwa': ['ONDO', 'CFG', 'POLYX'],
    }
    for cat, assets in categories.items():
        if base_asset in assets:
            return cat
    return 'other'
```

#### Phase 2: Backend Services (Days 4-7)

**Enhancement: MarketDataSync**
```python
# backend/services/market_data_sync.py
# EXISTING CODE + ENHANCEMENTS

class MarketDataSync:
    def __init__(self, sync_interval: int = 10):
        # ... existing code ...

        # ENHANCEMENT: Load all 448 assets from DB
        self.target_symbols = self._load_symbols_from_db()

        # ENHANCEMENT: Tier assignment
        self.tier1_symbols = self._get_tier_symbols(1)  # 50 assets
        self.tier2_symbols = self._get_tier_symbols(2)  # 150 assets
        self.tier3_symbols = self._get_tier_symbols(3)  # 248 assets

    def _load_symbols_from_db(self) -> List[str]:
        """Load active assets from database"""
        # Query DB for all active assets
        pass

    async def _sync_loop(self):
        """Enhanced loop with tiered updates"""
        iteration = 0
        while self._running:
            try:
                # Every iteration: Tier 1 (1-5s)
                await self._update_tier1()

                # Every 3 iterations: Tier 2 (10-15s)
                if iteration % 3 == 0:
                    await self._update_tier2()

                # Every 12 iterations: Tier 3 (60s)
                if iteration % 12 == 0:
                    await self._update_tier3()

                iteration += 1
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Market sync error: {e}")

    async def _update_tier1(self):
        """Update hot assets"""
        data = await self._fetch_symbols(self.tier1_symbols)
        await self.cache.set("markets:tier1", data, ttl=10)

    async def _update_tier2(self):
        """Update warm assets"""
        data = await self._fetch_symbols(self.tier2_symbols)
        await self.cache.set("markets:tier2", data, ttl=60)

    async def _update_tier3(self):
        """Update cold assets"""
        data = await self._fetch_symbols(self.tier3_symbols)
        await self.cache.set("markets:tier3", data, ttl=300)
```

**New Service: AssetRegistry**
```python
# backend/services/asset_registry.py

from sqlalchemy.orm import Session
from backend.data.models import Asset, AssetCategory

class AssetRegistry:
    """Central asset registry service"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_assets(
        self,
        category: Optional[str] = None,
        tier: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Asset]:
        query = self.db.query(Asset).filter(Asset.is_active == True)

        if category:
            query = query.filter(Asset.category == category)
        if tier:
            query = query.filter(Asset.tier == tier)
        if search:
            query = query.filter(
                or_(
                    Asset.symbol.ilike(f"%{search}%"),
                    Asset.base_asset.ilike(f"%{search}%"),
                    Asset.name.ilike(f"%{search}%")
                )
            )

        return query.offset(offset).limit(limit).all()

    def get_categories(self) -> List[AssetCategory]:
        return self.db.query(AssetCategory).order_by(AssetCategory.sort_order).all()

    def get_agent_watchlist(self, agent_id: str) -> List[Asset]:
        """Get assets watched by specific agent"""
        return self.db.query(Asset).join(
            AgentAssetWatchlist
        ).filter(
            AgentAssetWatchlist.agent_id == agent_id
        ).all()
```

#### Phase 3: API Endpoints (Days 8-10)

```python
# backend/api/assets_api.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/")
async def get_assets(
    category: Optional[str] = None,
    tier: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all assets with filtering"""
    registry = AssetRegistry(db)
    assets = registry.get_all_assets(
        category=category,
        tier=tier,
        search=search,
        limit=limit,
        offset=offset
    )
    return {
        "assets": assets,
        "total": registry.count_assets(category, tier, search),
        "limit": limit,
        "offset": offset
    }

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all asset categories"""
    registry = AssetRegistry(db)
    return registry.get_categories()

@router.get("/market-context")
async def get_market_context(
    tier: int = Query(1, description="Tier level (1=hot, 2=warm, 3=cold)"),
    cache: AsyncCacheLayer = Depends(get_cache)
):
    """Get current market context for specified tier"""
    data = await cache.get(f"markets:tier{tier}")
    return {
        "tier": tier,
        "timestamp": datetime.utcnow().isoformat(),
        "assets": data or [],
        "count": len(data) if data else 0
    }
```

#### Phase 4: Frontend (Days 11-14)

**Store Enhancement:**
```typescript
// frontend/src/store/assetStore.ts

interface AssetStore {
  // Existing
  assets: Asset[];

  // New
  allAssets: Asset[];
  assetCategories: Category[];
  assetsByCategory: Record<string, Asset[]>;
  selectedCategory: string | null;
  searchQuery: string;

  // Actions
  fetchAllAssets: () => Promise<void>;
  fetchCategories: () => Promise<void>;
  searchAssets: (query: string) => Asset[];
  filterByCategory: (category: string) => void;
}
```

**Component: AssetSelector**
```tsx
// frontend/src/components/AssetSelector.tsx

export function AssetSelector() {
  const { allAssets, categories, filterByCategory } = useAssetStore();

  return (
    <div className="asset-selector">
      <SearchBar />

      <div className="categories-grid">
        {categories.map(cat => (
          <CategoryDropdown
            key={cat.slug}
            title={cat.name}
            assets={assetsByCategory[cat.slug] || []}
            onSelect={handleAssetSelect}
          />
        ))}
      </div>
    </div>
  );
}
```

---

## 5. Resource & Time Estimation

### Time Breakdown

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| **Phase 1** | Database migrations | 2 days | Ready |
| | Seed 448 assets | 1 day | Ready |
| **Phase 2** | Enhance MarketDataSync | 2 days | Ready |
| | Create AssetRegistry | 1 day | Ready |
| | Agent context builder | 1 day | Ready |
| **Phase 3** | API endpoints | 2 days | Ready |
| **Phase 4** | Frontend store | 1 day | Ready |
| | AssetSelector component | 2 days | Ready |
| | Integration testing | 2 days | Ready |
| **Total** | | **14 days** | ✅ |

### Resource Requirements

| Component | Current | Needed | Action |
|-----------|---------|--------|--------|
| PostgreSQL | 2GB RAM | 2.1GB RAM | ✅ No change |
| Redis | 1.5GB RAM | 1.7GB RAM | ✅ Within limits |
| API Server | 3GB RAM | 3.2GB RAM | ✅ No change |
| Trading Engine | 4GB RAM | 4.5GB RAM | ⚠️ Monitor |

---

## 6. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bitvavo API rate limiting | Medium | High | Implement exponential backoff, cache aggressively |
| Redis memory overflow | Low | Medium | LRU policy active, monitor usage |
| Frontend performance | Medium | Medium | Virtualization, lazy loading |
| Database migration failure | Low | High | Test migrations, backup first |
| Agent overload | Medium | High | Context filtering, relevance scoring |

---

## 7. Success Criteria (Measurable)

- [ ] **Database:** 448 assets imported and queryable (< 100ms)
- [ ] **API:** /assets endpoint returns paginated results (< 200ms)
- [ ] **Redis:** Tiered keys working (tier1: 5s, tier2: 30s, tier3: 300s)
- [ ] **Agents:** Receive context updates within 2 seconds
- [ ] **Frontend:** Asset selector renders 448 assets without lag
- [ ] **Integration:** End-to-end flow works (select asset → see chart → agent responds)

---

## 8. Conclusion

**VERDICT: ✅ READY FOR IMPLEMENTATION**

De huidige infrastructuur is **volledig geschikt** voor de 448-asset implementatie. Er zijn geen blockers, alleen uitbreidingen op bestaande componenten.

**Aanbeveling:** Start met Phase 1 (Database) onmiddellijk. Dit is de foundation waarop alles else bouwt.

**Volgende stap:** Wil je dat ik begin met de database migraties (Phase 1)?
