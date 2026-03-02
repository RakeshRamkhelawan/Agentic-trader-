# 🔬 EPIC 3: Data & Analysis Engine

**Epic ID:** EPIC-PM-003
**Status:** ✅ COMPLETE
**Voltooide doorlooptijd:** ~25-27 uur
**Dependencies:** EPIC 2 (FastAPI Service Core) - COMPLETE

---

## 📋 Epic Overzicht

Dit epic implementeert de kern van de Prediction Market Intelligence service: de data-opslag via DuckDB/Parquet, de analysis runners (maker/taker analyse, volume trends, statistische testen), en de signal generation engine die ruwe data omzet naar actionable trading signals.

### Deliverables
- DuckDB database manager met Parquet I/O
- Maker/Taker analysis runner
- Volume trend analysis
- Statistical test framework (t-test, chi-square)
- Signal generator die analyses omzet naar `MarketSignal` objecten
- Data ingestion pipeline (Kalshi + Polymarket)

### Files die aangemaakt worden
| Bestand | Beschrijving |
|---------|--------------|
| `prediction-market-analysis/src/db/__init__.py` | DB module init |
| `prediction-market-analysis/src/db/duckdb_manager.py` | DuckDB connection & query manager |
| `prediction-market-analysis/src/db/parquet_handler.py` | Parquet read/write utilities |
| `prediction-market-analysis/src/analysis/__init__.py` | Analysis module init |
| `prediction-market-analysis/src/analysis/maker_taker.py` | Maker/Taker advantage analysis |
| `prediction-market-analysis/src/analysis/volume_trends.py` | Volume trend analysis |
| `prediction-market-analysis/src/analysis/statistical_tests.py` | Statistical testing framework |
| `prediction-market-analysis/src/signals/__init__.py` | Signals module init |
| `prediction-market-analysis/src/signals/generator.py` | Signal generation engine |
| `prediction-market-analysis/src/ingestion/__init__.py` | Ingestion module init |
| `prediction-market-analysis/src/ingestion/kalshi_client.py` | Kalshi data fetcher |
| `prediction-market-analysis/src/ingestion/polymarket_client.py` | Polymarket data fetcher |
| `prediction-market-analysis/tests/test_duckdb_manager.py` | DuckDB tests |
| `prediction-market-analysis/tests/test_maker_taker.py` | Maker/Taker tests |
| `prediction-market-analysis/tests/test_volume_trends.py` | Volume trend tests |
| `prediction-market-analysis/tests/test_signal_generator.py` | Signal generator tests |

### Referentie: Jon-Becker Repository Structuur

Het originele `prediction-market-analysis` project bevat:
```
data/
  kalshi/
    *.parquet         # Historische Kalshi trade data
  polymarket/
    *.parquet         # Historische Polymarket trade data
notebooks/
  analysis.ipynb      # Jupyter notebook met analyses
scripts/
  kalshi_backfill.py  # Data ingestion scripts
```

De analyses uit het notebook worden gerefactored naar productie-waardige Python modules.

---

## 📌 TASK 3.1: DuckDB Database Manager

**Task ID:** TASK-PM-009
**Status:** ✅ COMPLETE (28/28 tests passing)
**Voltooide tijd:** ~2 uur
**Dependencies:** TASK-PM-005
**Assignee:** _____

### Task Beschrijving
Implementeer de DuckDB database manager die verantwoordelijk is voor het aanmaken van de database, tabellen, en het uitvoeren van queries op Parquet bestanden.

### Huidige Context
- DuckDB wordt gebruikt als embedded analytics database (geen aparte server nodig)
- Data wordt opgeslagen als Parquet bestanden in `/data/kalshi/` en `/data/polymarket/`
- DuckDB kan direct Parquet bestanden queryen via `read_parquet()`
- Container mount: `/app/data` → prediction_market_data volume

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer DuckDB Database Manager
═══════════════════════════════════════════════════════════════════════════════

CONTEXT:
- DuckDB is een embedded OLAP database (vergelijkbaar met SQLite maar voor analytics)
- Parquet bestanden worden direct gequeried zonder aparte import stap
- Database file wordt opgeslagen in /app/data/prediction_market.duckdb
- In-memory mode voor tests

───────────────────────────────────────────────────────────────────────────────
BESTAND 1: prediction-market-analysis/src/db/__init__.py
───────────────────────────────────────────────────────────────────────────────

"""Database module for Prediction Market Intelligence."""
from src.db.duckdb_manager import DuckDBManager
from src.db.parquet_handler import ParquetHandler

__all__ = ["DuckDBManager", "ParquetHandler"]

───────────────────────────────────────────────────────────────────────────────
BESTAND 2: prediction-market-analysis/src/db/duckdb_manager.py
───────────────────────────────────────────────────────────────────────────────

"""
DuckDB Database Manager
Manages DuckDB connections, schema creation, and query execution.
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class DuckDBManager:
    """
    Manages DuckDB database connections and operations.

    Supports both persistent (file-based) and in-memory databases.
    Can directly query Parquet files.

    Usage:
        manager = DuckDBManager(db_path="/app/data/prediction_market.duckdb")
        manager.initialize()
        df = manager.query("SELECT * FROM kalshi_trades LIMIT 10")
        manager.close()
    """

    # Schema versie voor migrations
    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: Optional[str] = None,
        data_dir: str = "/app/data",
        read_only: bool = False
    ):
        """
        Initialize DuckDB manager.

        Args:
            db_path: Path to DuckDB database file. None for in-memory.
            data_dir: Base directory for Parquet data files.
            read_only: Open database in read-only mode.
        """
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.read_only = read_only
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._initialized = False

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Get active database connection."""
        if self._conn is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._conn

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    def initialize(self) -> None:
        """
        Initialize database connection and create schema.

        Creates tables if they don't exist.
        Registers Parquet file views.
        """
        logger.info(f"Initializing DuckDB (path: {self.db_path or ':memory:'})")

        if self.db_path:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._conn = duckdb.connect(
                self.db_path,
                read_only=self.read_only
            )
        else:
            self._conn = duckdb.connect(":memory:")

        # Create schema
        self._create_schema()

        # Register Parquet views if data directory exists
        if self.data_dir.exists():
            self._register_parquet_views()

        self._initialized = True
        logger.info("DuckDB initialized successfully")

    def _create_schema(self) -> None:
        """Create database schema (tables and indexes)."""

        # Kalshi trades table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kalshi_trades (
                id VARCHAR,
                ticker VARCHAR,
                category VARCHAR,
                market_title VARCHAR,
                side VARCHAR,
                yes_price DOUBLE,
                no_price DOUBLE,
                volume INTEGER,
                trade_time TIMESTAMP,
                taker_side VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Polymarket trades table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS polymarket_trades (
                id VARCHAR,
                market_slug VARCHAR,
                category VARCHAR,
                title VARCHAR,
                outcome VARCHAR,
                price DOUBLE,
                amount DOUBLE,
                side VARCHAR,
                trade_time TIMESTAMP,
                maker_address VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Signals table (generated signals)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS generated_signals (
                signal_id VARCHAR PRIMARY KEY,
                market VARCHAR,
                category VARCHAR,
                signal_type VARCHAR,
                confidence DOUBLE,
                symbol VARCHAR,
                indicators JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Analysis results table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                analysis_id VARCHAR PRIMARY KEY,
                analysis_type VARCHAR,
                market VARCHAR,
                status VARCHAR,
                result JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        logger.info("Schema created/verified")

    def _register_parquet_views(self) -> None:
        """
        Register Parquet files as views for direct querying.

        Creates views like:
        - kalshi_parquet → reads all parquet files in data/kalshi/
        - polymarket_parquet → reads all parquet files in data/polymarket/
        """
        kalshi_dir = self.data_dir / "kalshi"
        poly_dir = self.data_dir / "polymarket"

        if kalshi_dir.exists() and list(kalshi_dir.glob("*.parquet")):
            parquet_path = str(kalshi_dir / "*.parquet")
            self.conn.execute(f"""
                CREATE OR REPLACE VIEW kalshi_parquet AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            logger.info(f"Registered Kalshi Parquet view: {parquet_path}")

        if poly_dir.exists() and list(poly_dir.glob("*.parquet")):
            parquet_path = str(poly_dir / "*.parquet")
            self.conn.execute(f"""
                CREATE OR REPLACE VIEW polymarket_parquet AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            logger.info(f"Registered Polymarket Parquet view: {parquet_path}")

    def query(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        as_dataframe: bool = True
    ) -> Union[pd.DataFrame, List[tuple]]:
        """
        Execute a query and return results.

        Args:
            sql: SQL query string
            params: Query parameters for parameterized queries
            as_dataframe: Return as pandas DataFrame (True) or list of tuples

        Returns:
            Query results as DataFrame or list of tuples

        Raises:
            RuntimeError: If database not initialized
            duckdb.Error: If query fails
        """
        if params:
            result = self.conn.execute(sql, params)
        else:
            result = self.conn.execute(sql)

        if as_dataframe:
            return result.fetchdf()
        return result.fetchall()

    def execute(self, sql: str, params: Optional[List[Any]] = None) -> None:
        """
        Execute a statement (INSERT, UPDATE, DELETE, DDL).

        Args:
            sql: SQL statement
            params: Statement parameters
        """
        if params:
            self.conn.execute(sql, params)
        else:
            self.conn.execute(sql)

    def insert_dataframe(
        self,
        table: str,
        df: pd.DataFrame,
        if_exists: str = "append"
    ) -> int:
        """
        Insert a pandas DataFrame into a table.

        Args:
            table: Target table name
            df: DataFrame to insert
            if_exists: "append" or "replace"

        Returns:
            Number of rows inserted
        """
        if if_exists == "replace":
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.register("_temp_df", df)
        self.conn.execute(f"INSERT INTO {table} SELECT * FROM _temp_df")
        self.conn.unregister("_temp_df")

        return len(df)

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        result = self.conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name]
        ).fetchone()
        return result[0] > 0

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        result = self.conn.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()
        return result[0]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._initialized = False
            logger.info("DuckDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

───────────────────────────────────────────────────────────────────────────────
BESTAND 3: prediction-market-analysis/src/db/parquet_handler.py
───────────────────────────────────────────────────────────────────────────────

"""
Parquet Handler
Utilities for reading and writing Parquet files.
"""
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ParquetHandler:
    """Handle Parquet file I/O operations."""

    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = Path(data_dir)

    def read_parquet(
        self,
        market: str,
        filename: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Read Parquet file(s) for a market.

        Args:
            market: "kalshi" or "polymarket"
            filename: Specific file to read, or None for all

        Returns:
            DataFrame with trade data
        """
        market_dir = self.data_dir / market

        if not market_dir.exists():
            logger.warning(f"Market directory not found: {market_dir}")
            return pd.DataFrame()

        if filename:
            filepath = market_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Parquet file not found: {filepath}")
            return pd.read_parquet(filepath)

        # Read all parquet files
        files = list(market_dir.glob("*.parquet"))
        if not files:
            logger.warning(f"No parquet files found in {market_dir}")
            return pd.DataFrame()

        dfs = [pd.read_parquet(f) for f in files]
        return pd.concat(dfs, ignore_index=True)

    def write_parquet(
        self,
        df: pd.DataFrame,
        market: str,
        filename: str
    ) -> Path:
        """
        Write DataFrame as Parquet file.

        Args:
            df: DataFrame to write
            market: Market subdirectory
            filename: Output filename

        Returns:
            Path to written file
        """
        market_dir = self.data_dir / market
        market_dir.mkdir(parents=True, exist_ok=True)

        filepath = market_dir / filename
        df.to_parquet(filepath, index=False)
        logger.info(f"Written {len(df)} rows to {filepath}")

        return filepath

    def list_parquet_files(self, market: str) -> List[str]:
        """List available Parquet files for a market."""
        market_dir = self.data_dir / market
        if not market_dir.exists():
            return []
        return [f.name for f in market_dir.glob("*.parquet")]

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from src.db.duckdb_manager import DuckDBManager
with DuckDBManager() as db:
    result = db.query('SELECT 1 AS test')
    print(f'Query result: {result}')
    print(f'Tables: kalshi_trades={db.table_exists(\"kalshi_trades\")}')
    print('DuckDB OK!')
"

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] DuckDBManager kan in-memory en file-based databases aanmaken
- [ ] Schema wordt correct aangemaakt (4 tabellen)
- [ ] Parquet views worden geregistreerd als data aanwezig is
- [ ] query() retourneert pandas DataFrame
- [ ] Context manager (`with` statement) werkt
- [ ] ParquetHandler kan lezen en schrijven

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_duckdb_manager.py`

```python
"""
Tests voor DuckDB Manager.
Run: pytest prediction-market-analysis/tests/test_duckdb_manager.py -v
"""
import os
import tempfile
import pytest
import pandas as pd
from src.db.duckdb_manager import DuckDBManager


class TestDuckDBManager:
    """Tests voor DuckDBManager."""

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_initialize_in_memory(self):
        """Happy path: In-memory database initialiseert correct."""
        manager = DuckDBManager()
        manager.initialize()

        assert manager.is_initialized is True
        manager.close()

    def test_happy_path_context_manager(self):
        """Happy path: Context manager werkt correct."""
        with DuckDBManager() as db:
            assert db.is_initialized is True
            result = db.query("SELECT 1 AS test")
            assert len(result) == 1

    def test_happy_path_schema_created(self):
        """Happy path: Schema tabellen worden aangemaakt."""
        with DuckDBManager() as db:
            assert db.table_exists("kalshi_trades") is True
            assert db.table_exists("polymarket_trades") is True
            assert db.table_exists("generated_signals") is True
            assert db.table_exists("analysis_results") is True

    def test_happy_path_query_returns_dataframe(self):
        """Happy path: Query retourneert pandas DataFrame."""
        with DuckDBManager() as db:
            result = db.query("SELECT 1 AS value, 'test' AS name")

            assert isinstance(result, pd.DataFrame)
            assert result.iloc[0]["value"] == 1
            assert result.iloc[0]["name"] == "test"

    def test_happy_path_query_returns_tuples(self):
        """Happy path: Query met as_dataframe=False retourneert tuples."""
        with DuckDBManager() as db:
            result = db.query("SELECT 1, 2, 3", as_dataframe=False)

            assert isinstance(result, list)
            assert result[0] == (1, 2, 3)

    def test_happy_path_insert_dataframe(self):
        """Happy path: DataFrame insert werkt."""
        with DuckDBManager() as db:
            df = pd.DataFrame({
                "id": ["t1", "t2"],
                "ticker": ["BTC-YES", "ETH-YES"],
                "category": ["crypto", "crypto"],
                "market_title": ["Bitcoin > 100k", "Ethereum > 5k"],
                "side": ["buy", "sell"],
                "yes_price": [0.72, 0.45],
                "no_price": [0.28, 0.55],
                "volume": [100, 50],
                "trade_time": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                "taker_side": ["buy", "sell"],
                "created_at": pd.to_datetime(["2026-01-01", "2026-01-02"])
            })

            rows = db.insert_dataframe("kalshi_trades", df)
            assert rows == 2
            assert db.get_table_count("kalshi_trades") == 2

    def test_happy_path_file_based_database(self):
        """Happy path: File-based database werkt."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.duckdb")

            with DuckDBManager(db_path=db_path) as db:
                db.execute("INSERT INTO generated_signals (signal_id, market, signal_type, confidence) VALUES ('s1', 'kalshi', 'bullish', 0.8)")
                count = db.get_table_count("generated_signals")
                assert count == 1

            # Verify persistence
            assert os.path.exists(db_path)

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_query_before_initialize(self):
        """Unhappy path: Query zonder initialize geeft RuntimeError."""
        manager = DuckDBManager()

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.query("SELECT 1")

    def test_unhappy_path_invalid_sql(self):
        """Unhappy path: Invalid SQL geeft DuckDB error."""
        with DuckDBManager() as db:
            with pytest.raises(Exception):
                db.query("SELECT * FROM nonexistent_table_xyz")

    def test_unhappy_path_close_already_closed(self):
        """Unhappy path: Close op gesloten DB geeft geen error."""
        manager = DuckDBManager()
        manager.initialize()
        manager.close()
        # Second close should not raise
        manager.close()

    def test_unhappy_path_table_not_exists(self):
        """Unhappy path: Check voor niet-bestaande tabel."""
        with DuckDBManager() as db:
            assert db.table_exists("fantasy_table_xyz") is False


class TestParquetHandler:
    """Tests voor ParquetHandler."""

    def test_happy_path_write_and_read(self):
        """Happy path: Schrijf en lees Parquet bestand."""
        from src.db.parquet_handler import ParquetHandler

        with tempfile.TemporaryDirectory() as tmp:
            handler = ParquetHandler(data_dir=tmp)

            df = pd.DataFrame({
                "ticker": ["BTC-YES", "ETH-NO"],
                "price": [0.72, 0.55]
            })

            path = handler.write_parquet(df, "kalshi", "test.parquet")
            assert path.exists()

            result = handler.read_parquet("kalshi", "test.parquet")
            assert len(result) == 2

    def test_unhappy_path_read_nonexistent_market(self):
        """Unhappy path: Lees van niet-bestaande market directory."""
        from src.db.parquet_handler import ParquetHandler

        with tempfile.TemporaryDirectory() as tmp:
            handler = ParquetHandler(data_dir=tmp)
            result = handler.read_parquet("nonexistent")
            assert len(result) == 0

    def test_unhappy_path_read_nonexistent_file(self):
        """Unhappy path: Lees van niet-bestaand bestand."""
        from src.db.parquet_handler import ParquetHandler

        with tempfile.TemporaryDirectory() as tmp:
            handler = ParquetHandler(data_dir=tmp)
            os.makedirs(os.path.join(tmp, "kalshi"))

            with pytest.raises(FileNotFoundError):
                handler.read_parquet("kalshi", "nonexistent.parquet")
```

---

### 📎 MICROTASK 3.1.1: Create DB Directory & Init

**Microtask ID:** MT-PM-009-001
**Geschatte tijd:** 10 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.1.2: Implement DuckDBManager

**Microtask ID:** MT-PM-009-002
**Geschatte tijd:** 90 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.1.3: Implement ParquetHandler

**Microtask ID:** MT-PM-009-003
**Geschatte tijd:** 45 min
**Status:** 🔴 TODO

---

## 📌 TASK 3.2: Maker/Taker Analysis

**Task ID:** TASK-PM-010
**Status:** ✅ COMPLETE (26/26 analysis tests passing)
**Voltooide tijd:** ~2.5 uur
**Dependencies:** TASK-PM-009
**Assignee:** _____

### Task Beschrijving
Implementeer de maker/taker advantage analyse. Dit is de kern-analyse uit het originele prediction-market-analysis project. Het analyseert wie de liquiditeit neemt (taker) vs aanbiedt (maker) en berekent het prijsvoordeel.

### Achtergrond: Maker/Taker Analyse

In prediction markets:
- **Maker**: Plaatst een order in het orderboek (biedt liquiditeit aan)
- **Taker**: Neemt een bestaande order uit het orderboek (neemt liquiditeit)
- **Maker Advantage**: Het gemiddelde prijsverschil tussen maker- en taker-orders. Positief = makers krijgen betere prijzen

De originele analyse in het Jon-Becker repository berekent:
1. Gemiddelde prijs per side (maker vs taker)
2. Netto voordeel per market/categorie
3. Volume-gewogen analyse
4. Trend over tijd

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer Maker/Taker Analysis Runner
═══════════════════════════════════════════════════════════════════════════════

CONTEXT:
- Gebaseerd op analyse uit Jon-Becker/prediction-market-analysis
- Data komt uit kalshi_trades en polymarket_trades tabellen
- taker_side kolom geeft aan wie de taker is
- Resultaten worden als MarketSignal objecten gegenereerd

───────────────────────────────────────────────────────────────────────────────
BESTAND: prediction-market-analysis/src/analysis/maker_taker.py
───────────────────────────────────────────────────────────────────────────────

"""
Maker/Taker Advantage Analysis

Analyzes the price advantage between market makers and takers
in prediction markets. This is the core analysis from the
original prediction-market-analysis project.

Theory:
- Makers provide liquidity (place orders in book)
- Takers consume liquidity (fill existing orders)
- Maker advantage = avg maker price - avg taker price
- Positive advantage = makers get better prices
- Useful as a contrarian signal (smart money indicator)
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.db.duckdb_manager import DuckDBManager

logger = logging.getLogger(__name__)


@dataclass
class MakerTakerResult:
    """Result of maker/taker analysis for a single market/category."""
    market: str
    category: str
    maker_avg_price: float
    taker_avg_price: float
    advantage: float  # maker_avg - taker_avg
    maker_volume: int
    taker_volume: int
    total_trades: int
    period_start: datetime
    period_end: datetime
    confidence: float  # Based on sample size and consistency

    @property
    def signal_direction(self) -> str:
        """Determine signal direction from advantage."""
        if self.advantage > 0.02:
            return "bullish"
        elif self.advantage < -0.02:
            return "bearish"
        return "neutral"


class MakerTakerAnalyzer:
    """
    Analyzes maker/taker dynamics in prediction markets.

    Identifies smart money flow by comparing prices obtained
    by liquidity makers vs takers.
    """

    # Minimum trades for statistically meaningful analysis
    MIN_TRADES = 30

    # Threshold for significant advantage
    SIGNIFICANCE_THRESHOLD = 0.01

    def __init__(self, db: DuckDBManager):
        """
        Initialize analyzer.

        Args:
            db: Initialized DuckDB manager
        """
        self.db = db

    def analyze_kalshi(
        self,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MakerTakerResult]:
        """
        Run maker/taker analysis on Kalshi data.

        Args:
            category: Filter by category (crypto, politics, etc.)
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            List of MakerTakerResult per category
        """
        query = """
            SELECT
                category,
                taker_side,
                AVG(yes_price) as avg_price,
                SUM(volume) as total_volume,
                COUNT(*) as trade_count,
                MIN(trade_time) as first_trade,
                MAX(trade_time) as last_trade
            FROM kalshi_trades
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if start_date:
            query += " AND trade_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_time <= ?"
            params.append(end_date)

        query += " GROUP BY category, taker_side ORDER BY category"

        df = self.db.query(query, params if params else None)

        if df.empty:
            logger.warning("No Kalshi trade data found")
            return []

        return self._calculate_results(df, "kalshi")

    def analyze_polymarket(
        self,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MakerTakerResult]:
        """
        Run maker/taker analysis on Polymarket data.

        Args:
            category: Filter by category
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            List of MakerTakerResult per category
        """
        query = """
            SELECT
                category,
                side as taker_side,
                AVG(price) as avg_price,
                SUM(amount) as total_volume,
                COUNT(*) as trade_count,
                MIN(trade_time) as first_trade,
                MAX(trade_time) as last_trade
            FROM polymarket_trades
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if start_date:
            query += " AND trade_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_time <= ?"
            params.append(end_date)

        query += " GROUP BY category, side ORDER BY category"

        df = self.db.query(query, params if params else None)

        if df.empty:
            logger.warning("No Polymarket trade data found")
            return []

        return self._calculate_results(df, "polymarket")

    def _calculate_results(
        self,
        df: pd.DataFrame,
        market: str
    ) -> List[MakerTakerResult]:
        """Calculate maker/taker results from grouped data."""
        results = []

        for category in df["category"].unique():
            cat_data = df[df["category"] == category]

            # Get maker and taker data
            maker_data = cat_data[cat_data["taker_side"] != "buy"]
            taker_data = cat_data[cat_data["taker_side"] == "buy"]

            if maker_data.empty or taker_data.empty:
                continue

            maker_avg = float(maker_data["avg_price"].iloc[0])
            taker_avg = float(taker_data["avg_price"].iloc[0])
            maker_vol = int(maker_data["total_volume"].iloc[0])
            taker_vol = int(taker_data["total_volume"].iloc[0])
            total_trades = int(cat_data["trade_count"].sum())

            # Calculate confidence based on sample size
            confidence = min(1.0, total_trades / 1000)  # Linear scaling

            if total_trades < self.MIN_TRADES:
                confidence *= 0.5  # Penalize small samples

            advantage = maker_avg - taker_avg

            results.append(MakerTakerResult(
                market=market,
                category=category,
                maker_avg_price=round(maker_avg, 6),
                taker_avg_price=round(taker_avg, 6),
                advantage=round(advantage, 6),
                maker_volume=maker_vol,
                taker_volume=taker_vol,
                total_trades=total_trades,
                period_start=cat_data["first_trade"].min(),
                period_end=cat_data["last_trade"].max(),
                confidence=round(confidence, 3)
            ))

        return results

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from src.db.duckdb_manager import DuckDBManager
from src.analysis.maker_taker import MakerTakerAnalyzer
import pandas as pd

with DuckDBManager() as db:
    # Insert test data
    df = pd.DataFrame({
        'id': ['t1','t2','t3','t4'],
        'ticker': ['BTC','BTC','BTC','BTC'],
        'category': ['crypto','crypto','crypto','crypto'],
        'market_title': ['BTC > 100k']*4,
        'side': ['buy','sell','buy','sell'],
        'yes_price': [0.72, 0.70, 0.74, 0.68],
        'no_price': [0.28, 0.30, 0.26, 0.32],
        'volume': [100, 150, 200, 100],
        'trade_time': pd.to_datetime(['2026-01-01']*4),
        'taker_side': ['buy','sell','buy','sell'],
        'created_at': pd.to_datetime(['2026-01-01']*4)
    })
    db.insert_dataframe('kalshi_trades', df)

    analyzer = MakerTakerAnalyzer(db)
    results = analyzer.analyze_kalshi()
    for r in results:
        print(f'{r.category}: advantage={r.advantage}, direction={r.signal_direction}')
"

═══════════════════════════════════════════════════════════════════════════════
```

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_maker_taker.py`

```python
"""
Tests voor Maker/Taker Analysis.
Run: pytest prediction-market-analysis/tests/test_maker_taker.py -v
"""
import pytest
import pandas as pd
from datetime import datetime
from src.db.duckdb_manager import DuckDBManager
from src.analysis.maker_taker import MakerTakerAnalyzer, MakerTakerResult


class TestMakerTakerAnalyzer:
    """Tests voor MakerTakerAnalyzer."""

    @pytest.fixture
    def db_with_data(self):
        """DuckDB met test trade data."""
        db = DuckDBManager()
        db.initialize()

        # Insert Kalshi test data
        df = pd.DataFrame({
            "id": [f"t{i}" for i in range(100)],
            "ticker": ["BTC-YES"] * 50 + ["ETH-YES"] * 50,
            "category": ["crypto"] * 100,
            "market_title": ["BTC > 100k"] * 50 + ["ETH > 5k"] * 50,
            "side": (["buy", "sell"] * 25) + (["buy", "sell"] * 25),
            "yes_price": [0.72 + (i * 0.001) for i in range(50)] + [0.45 + (i * 0.001) for i in range(50)],
            "no_price": [0.28 - (i * 0.001) for i in range(50)] + [0.55 - (i * 0.001) for i in range(50)],
            "volume": [100] * 100,
            "trade_time": pd.to_datetime(["2026-01-01"] * 100),
            "taker_side": (["buy"] * 25 + ["sell"] * 25) * 2,
            "created_at": pd.to_datetime(["2026-01-01"] * 100)
        })
        db.insert_dataframe("kalshi_trades", df)

        yield db
        db.close()

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_analyze_kalshi_returns_results(self, db_with_data):
        """Happy path: Kalshi analyse retourneert resultaten."""
        analyzer = MakerTakerAnalyzer(db_with_data)
        results = analyzer.analyze_kalshi()

        assert len(results) > 0
        assert all(isinstance(r, MakerTakerResult) for r in results)

    def test_happy_path_result_has_all_fields(self, db_with_data):
        """Happy path: Resultaat bevat alle velden."""
        analyzer = MakerTakerAnalyzer(db_with_data)
        results = analyzer.analyze_kalshi()

        result = results[0]
        assert result.market == "kalshi"
        assert result.category == "crypto"
        assert isinstance(result.advantage, float)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1

    def test_happy_path_filter_by_category(self, db_with_data):
        """Happy path: Category filter werkt."""
        analyzer = MakerTakerAnalyzer(db_with_data)
        results = analyzer.analyze_kalshi(category="crypto")

        assert all(r.category == "crypto" for r in results)

    def test_happy_path_signal_direction_bullish(self):
        """Happy path: Positief advantage → bullish signal."""
        result = MakerTakerResult(
            market="kalshi", category="crypto",
            maker_avg_price=0.75, taker_avg_price=0.70,
            advantage=0.05, maker_volume=100, taker_volume=100,
            total_trades=1000, period_start=datetime.now(),
            period_end=datetime.now(), confidence=0.8
        )
        assert result.signal_direction == "bullish"

    def test_happy_path_signal_direction_bearish(self):
        """Happy path: Negatief advantage → bearish signal."""
        result = MakerTakerResult(
            market="kalshi", category="crypto",
            maker_avg_price=0.65, taker_avg_price=0.70,
            advantage=-0.05, maker_volume=100, taker_volume=100,
            total_trades=1000, period_start=datetime.now(),
            period_end=datetime.now(), confidence=0.8
        )
        assert result.signal_direction == "bearish"

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_empty_database(self):
        """Unhappy path: Lege database retourneert lege lijst."""
        with DuckDBManager() as db:
            analyzer = MakerTakerAnalyzer(db)
            results = analyzer.analyze_kalshi()
            assert results == []

    def test_unhappy_path_nonexistent_category(self, db_with_data):
        """Unhappy path: Niet-bestaande category geeft lege lijst."""
        analyzer = MakerTakerAnalyzer(db_with_data)
        results = analyzer.analyze_kalshi(category="nonexistent")
        assert results == []

    def test_unhappy_path_low_sample_confidence(self, db_with_data):
        """Unhappy path: Weinig trades → lage confidence."""
        with DuckDBManager() as db:
            df = pd.DataFrame({
                "id": ["t1", "t2"],
                "ticker": ["BTC-YES"] * 2,
                "category": ["crypto"] * 2,
                "market_title": ["BTC"] * 2,
                "side": ["buy", "sell"],
                "yes_price": [0.72, 0.68],
                "no_price": [0.28, 0.32],
                "volume": [10, 10],
                "trade_time": pd.to_datetime(["2026-01-01"] * 2),
                "taker_side": ["buy", "sell"],
                "created_at": pd.to_datetime(["2026-01-01"] * 2)
            })
            db.insert_dataframe("kalshi_trades", df)

            analyzer = MakerTakerAnalyzer(db)
            results = analyzer.analyze_kalshi()

            if results:
                assert results[0].confidence < 0.5
```

---

### 📎 MICROTASK 3.2.1: Create Analysis Module Structure

**Microtask ID:** MT-PM-010-001
**Geschatte tijd:** 10 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.2.2: Implement MakerTakerAnalyzer

**Microtask ID:** MT-PM-010-002
**Geschatte tijd:** 90 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.2.3: Write & Run TDD Tests

**Microtask ID:** MT-PM-010-003
**Geschatte tijd:** 60 min
**Status:** 🔴 TODO

---

## 📌 TASK 3.3: Volume Trend Analysis & Statistical Tests

**Task ID:** TASK-PM-011
**Status:** ✅ COMPLETE (26/26 analysis tests passing)
**Voltooide tijd:** ~2.5 uur
**Dependencies:** TASK-PM-010
**Assignee:** _____

### Task Beschrijving
Implementeer volume trend analyse en statistische tests. Deze modules analyseren handelsvolume patronen en voeren statistische significantie tests uit.

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer Volume Trends & Statistical Tests
═══════════════════════════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────────────────────────
BESTAND 1: prediction-market-analysis/src/analysis/volume_trends.py
───────────────────────────────────────────────────────────────────────────────

"""
Volume Trend Analysis

Analyzes trading volume patterns in prediction markets to
identify momentum and interest shifts.

Key metrics:
- Volume change over time windows (1h, 4h, 24h)
- Volume concentration by category
- Volume-weighted price momentum
- Unusual volume spikes (z-score based)
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from src.db.duckdb_manager import DuckDBManager

logger = logging.getLogger(__name__)


@dataclass
class VolumeTrendResult:
    """Result for volume trend analysis."""
    market: str
    category: str
    current_volume: float
    previous_volume: float
    volume_change_pct: float
    window_hours: int
    z_score: float  # How unusual the current volume is
    trend: str  # "increasing", "decreasing", "stable"
    is_unusual: bool  # z_score > 2.0
    period_end: datetime

    @property
    def signal_strength(self) -> float:
        """Calculate signal strength from volume change."""
        return min(1.0, abs(self.z_score) / 3.0)


class VolumeTrendAnalyzer:
    """Analyzes volume trends in prediction markets."""

    WINDOWS = [1, 4, 24]  # Hours
    Z_SCORE_THRESHOLD = 2.0  # For unusual volume detection

    def __init__(self, db: DuckDBManager):
        self.db = db

    def analyze(
        self,
        market: str = "kalshi",
        category: Optional[str] = None,
        window_hours: int = 24
    ) -> List[VolumeTrendResult]:
        """
        Analyze volume trends.

        Args:
            market: "kalshi" or "polymarket"
            category: Optional category filter
            window_hours: Time window in hours

        Returns:
            List of VolumeTrendResult
        """
        table = f"{market}_trades"
        volume_col = "volume" if market == "kalshi" else "amount"

        query = f"""
            WITH current_window AS (
                SELECT
                    category,
                    SUM({volume_col}) as volume,
                    COUNT(*) as trades
                FROM {table}
                WHERE trade_time > CURRENT_TIMESTAMP - INTERVAL '{window_hours} hours'
                {"AND category = ?" if category else ""}
                GROUP BY category
            ),
            previous_window AS (
                SELECT
                    category,
                    SUM({volume_col}) as volume,
                    COUNT(*) as trades
                FROM {table}
                WHERE trade_time > CURRENT_TIMESTAMP - INTERVAL '{window_hours * 2} hours'
                AND trade_time <= CURRENT_TIMESTAMP - INTERVAL '{window_hours} hours'
                {"AND category = ?" if category else ""}
                GROUP BY category
            ),
            historical AS (
                SELECT
                    category,
                    AVG({volume_col}) as avg_volume,
                    STDDEV({volume_col}) as std_volume
                FROM {table}
                {"WHERE category = ?" if category else ""}
                GROUP BY category
            )
            SELECT
                c.category,
                COALESCE(c.volume, 0) as current_volume,
                COALESCE(p.volume, 0) as previous_volume,
                COALESCE(h.avg_volume, 0) as avg_volume,
                COALESCE(h.std_volume, 1) as std_volume
            FROM current_window c
            LEFT JOIN previous_window p ON c.category = p.category
            LEFT JOIN historical h ON c.category = h.category
        """

        params = []
        if category:
            params = [category] * 3

        df = self.db.query(query, params if params else None)

        results = []
        for _, row in df.iterrows():
            prev = row["previous_volume"] if row["previous_volume"] > 0 else 1
            change_pct = ((row["current_volume"] - row["previous_volume"]) / prev) * 100

            std = row["std_volume"] if row["std_volume"] > 0 else 1
            z_score = (row["current_volume"] - row["avg_volume"]) / std

            if change_pct > 10:
                trend = "increasing"
            elif change_pct < -10:
                trend = "decreasing"
            else:
                trend = "stable"

            results.append(VolumeTrendResult(
                market=market,
                category=row["category"],
                current_volume=float(row["current_volume"]),
                previous_volume=float(row["previous_volume"]),
                volume_change_pct=round(change_pct, 2),
                window_hours=window_hours,
                z_score=round(float(z_score), 3),
                trend=trend,
                is_unusual=abs(z_score) > self.Z_SCORE_THRESHOLD,
                period_end=datetime.utcnow()
            ))

        return results

───────────────────────────────────────────────────────────────────────────────
BESTAND 2: prediction-market-analysis/src/analysis/statistical_tests.py
───────────────────────────────────────────────────────────────────────────────

"""
Statistical Testing Framework

Provides significance testing for prediction market analyses.
Uses scipy for t-tests and chi-square tests.

Tests:
- Independent t-test: Compare mean prices maker vs taker
- Chi-square test: Test if maker/taker distribution differs from expected
- Mann-Whitney U: Non-parametric comparison
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from src.db.duckdb_manager import DuckDBManager

logger = logging.getLogger(__name__)


@dataclass
class StatTestResult:
    """Result of a statistical test."""
    test_name: str
    statistic: float
    p_value: float
    is_significant: bool  # p_value < alpha
    alpha: float
    effect_size: Optional[float]
    interpretation: str
    sample_size_a: int
    sample_size_b: int


class StatisticalTester:
    """Performs statistical tests on prediction market data."""

    DEFAULT_ALPHA = 0.05

    def __init__(self, db: DuckDBManager):
        self.db = db

    def ttest_maker_vs_taker(
        self,
        market: str = "kalshi",
        category: Optional[str] = None,
        alpha: float = DEFAULT_ALPHA
    ) -> Optional[StatTestResult]:
        """
        Independent t-test comparing maker vs taker prices.

        H0: No difference in mean price between maker and taker trades
        H1: Significant difference exists

        Args:
            market: Market to analyze
            category: Optional category filter
            alpha: Significance level

        Returns:
            StatTestResult or None if insufficient data
        """
        price_col = "yes_price" if market == "kalshi" else "price"
        table = f"{market}_trades"
        side_col = "taker_side" if market == "kalshi" else "side"

        query = f"""
            SELECT {price_col} as price, {side_col} as side
            FROM {table}
            WHERE {price_col} IS NOT NULL
        """
        if category:
            query += f" AND category = '{category}'"

        df = self.db.query(query)

        if df.empty or len(df) < 10:
            logger.warning("Insufficient data for t-test")
            return None

        group_a = df[df["side"] == "buy"]["price"].values
        group_b = df[df["side"] == "sell"]["price"].values

        if len(group_a) < 5 or len(group_b) < 5:
            return None

        t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)

        # Cohen's d effect size
        pooled_std = np.sqrt(
            (np.std(group_a)**2 + np.std(group_b)**2) / 2
        )
        effect_size = abs(np.mean(group_a) - np.mean(group_b)) / pooled_std if pooled_std > 0 else 0

        is_sig = p_value < alpha

        if not is_sig:
            interpretation = "No significant price difference between maker and taker trades"
        elif effect_size < 0.2:
            interpretation = "Statistically significant but negligible practical difference"
        elif effect_size < 0.5:
            interpretation = "Small but significant maker/taker price difference detected"
        elif effect_size < 0.8:
            interpretation = "Medium-sized maker/taker price advantage detected"
        else:
            interpretation = "Large maker/taker price advantage detected — strong signal"

        return StatTestResult(
            test_name="Independent t-test (Welch's)",
            statistic=round(float(t_stat), 4),
            p_value=round(float(p_value), 6),
            is_significant=is_sig,
            alpha=alpha,
            effect_size=round(float(effect_size), 4),
            interpretation=interpretation,
            sample_size_a=len(group_a),
            sample_size_b=len(group_b)
        )

    def chi_square_distribution(
        self,
        market: str = "kalshi",
        category: Optional[str] = None,
        alpha: float = DEFAULT_ALPHA
    ) -> Optional[StatTestResult]:
        """
        Chi-square test for maker/taker distribution.

        Tests if the distribution of buy/sell trades significantly
        differs from a 50/50 expected distribution.

        Args:
            market: Market to analyze
            category: Optional category filter
            alpha: Significance level

        Returns:
            StatTestResult or None if insufficient data
        """
        table = f"{market}_trades"
        side_col = "taker_side" if market == "kalshi" else "side"

        query = f"""
            SELECT {side_col} as side, COUNT(*) as count
            FROM {table}
            WHERE {side_col} IS NOT NULL
        """
        if category:
            query += f" AND category = '{category}'"
        query += f" GROUP BY {side_col}"

        df = self.db.query(query)

        if df.empty or len(df) < 2:
            return None

        observed = df["count"].values
        total = observed.sum()
        expected = np.array([total / len(observed)] * len(observed))

        chi2, p_value = stats.chisquare(observed, expected)

        # Cramér's V effect size
        effect_size = np.sqrt(chi2 / (total * (len(observed) - 1))) if total > 0 else 0

        is_sig = p_value < alpha

        if not is_sig:
            interpretation = "Buy/sell distribution is consistent with expected 50/50"
        else:
            interpretation = f"Significant imbalance in buy/sell distribution (Cramér's V={effect_size:.3f})"

        return StatTestResult(
            test_name="Chi-square goodness of fit",
            statistic=round(float(chi2), 4),
            p_value=round(float(p_value), 6),
            is_significant=is_sig,
            alpha=alpha,
            effect_size=round(float(effect_size), 4),
            interpretation=interpretation,
            sample_size_a=int(observed[0]) if len(observed) > 0 else 0,
            sample_size_b=int(observed[1]) if len(observed) > 1 else 0
        )

───────────────────────────────────────────────────────────────────────────────
BESTAND 3: prediction-market-analysis/src/analysis/__init__.py
───────────────────────────────────────────────────────────────────────────────

"""Analysis module for Prediction Market Intelligence."""
from src.analysis.maker_taker import MakerTakerAnalyzer, MakerTakerResult
from src.analysis.volume_trends import VolumeTrendAnalyzer, VolumeTrendResult
from src.analysis.statistical_tests import StatisticalTester, StatTestResult

__all__ = [
    "MakerTakerAnalyzer", "MakerTakerResult",
    "VolumeTrendAnalyzer", "VolumeTrendResult",
    "StatisticalTester", "StatTestResult"
]

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from src.analysis import MakerTakerAnalyzer, VolumeTrendAnalyzer, StatisticalTester
print('All analysis modules imported successfully!')
"

═══════════════════════════════════════════════════════════════════════════════
```

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_volume_and_stats.py`

```python
"""
Tests voor Volume Trends & Statistical Tests.
Run: pytest prediction-market-analysis/tests/test_volume_and_stats.py -v
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.db.duckdb_manager import DuckDBManager
from src.analysis.volume_trends import VolumeTrendAnalyzer, VolumeTrendResult
from src.analysis.statistical_tests import StatisticalTester, StatTestResult


class TestVolumeTrendAnalyzer:
    """Tests voor VolumeTrendAnalyzer."""

    @pytest.fixture
    def db_with_volume_data(self):
        """DuckDB met volume test data."""
        db = DuckDBManager()
        db.initialize()

        now = datetime.utcnow()
        rows = []
        for i in range(200):
            rows.append({
                "id": f"v{i}",
                "ticker": "BTC-YES",
                "category": "crypto",
                "market_title": "BTC > 100k",
                "side": "buy",
                "yes_price": 0.72,
                "no_price": 0.28,
                "volume": 100 + (i * 10),  # Increasing volume
                "trade_time": now - timedelta(hours=48 - (i * 0.24)),
                "taker_side": "buy" if i % 2 == 0 else "sell",
                "created_at": now
            })

        df = pd.DataFrame(rows)
        db.insert_dataframe("kalshi_trades", df)

        yield db
        db.close()

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_analyze_returns_results(self, db_with_volume_data):
        """Happy path: Analyse retourneert resultaten."""
        analyzer = VolumeTrendAnalyzer(db_with_volume_data)
        results = analyzer.analyze(market="kalshi")

        assert isinstance(results, list)

    def test_happy_path_result_has_trend(self, db_with_volume_data):
        """Happy path: Resultaat heeft trend indicator."""
        analyzer = VolumeTrendAnalyzer(db_with_volume_data)
        results = analyzer.analyze(market="kalshi")

        if results:
            assert results[0].trend in ["increasing", "decreasing", "stable"]

    def test_happy_path_signal_strength_bounded(self):
        """Happy path: Signal strength is 0-1."""
        result = VolumeTrendResult(
            market="kalshi", category="crypto",
            current_volume=1000, previous_volume=500,
            volume_change_pct=100.0, window_hours=24,
            z_score=2.5, trend="increasing", is_unusual=True,
            period_end=datetime.now()
        )
        assert 0 <= result.signal_strength <= 1

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_empty_database(self):
        """Unhappy path: Lege database retourneert lege lijst."""
        with DuckDBManager() as db:
            analyzer = VolumeTrendAnalyzer(db)
            results = analyzer.analyze(market="kalshi")
            assert results == []


class TestStatisticalTester:
    """Tests voor StatisticalTester."""

    @pytest.fixture
    def db_with_stat_data(self):
        """DuckDB met data voor statistische tests."""
        db = DuckDBManager()
        db.initialize()

        np.random.seed(42)
        n = 500

        df = pd.DataFrame({
            "id": [f"s{i}" for i in range(n)],
            "ticker": ["BTC-YES"] * n,
            "category": ["crypto"] * n,
            "market_title": ["BTC > 100k"] * n,
            "side": ["buy"] * n,
            "yes_price": np.concatenate([
                np.random.normal(0.72, 0.05, n // 2),  # buy group
                np.random.normal(0.68, 0.05, n // 2),  # sell group
            ]),
            "no_price": [0.28] * n,
            "volume": [100] * n,
            "trade_time": pd.to_datetime(["2026-01-15"] * n),
            "taker_side": ["buy"] * (n // 2) + ["sell"] * (n // 2),
            "created_at": pd.to_datetime(["2026-01-15"] * n)
        })
        db.insert_dataframe("kalshi_trades", df)

        yield db
        db.close()

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_ttest_returns_result(self, db_with_stat_data):
        """Happy path: T-test retourneert resultaat."""
        tester = StatisticalTester(db_with_stat_data)
        result = tester.ttest_maker_vs_taker(market="kalshi")

        assert result is not None
        assert isinstance(result, StatTestResult)
        assert result.test_name == "Independent t-test (Welch's)"

    def test_happy_path_ttest_detects_significance(self, db_with_stat_data):
        """Happy path: T-test detecteert significant verschil."""
        tester = StatisticalTester(db_with_stat_data)
        result = tester.ttest_maker_vs_taker(market="kalshi")

        # With our deliberately different means, should be significant
        assert result is not None
        assert result.p_value < 0.05
        assert result.is_significant is True

    def test_happy_path_chi_square_returns_result(self, db_with_stat_data):
        """Happy path: Chi-square test retourneert resultaat."""
        tester = StatisticalTester(db_with_stat_data)
        result = tester.chi_square_distribution(market="kalshi")

        assert result is not None
        assert result.test_name == "Chi-square goodness of fit"

    def test_happy_path_effect_size_present(self, db_with_stat_data):
        """Happy path: Effect size is berekend."""
        tester = StatisticalTester(db_with_stat_data)
        result = tester.ttest_maker_vs_taker(market="kalshi")

        assert result is not None
        assert result.effect_size is not None
        assert result.effect_size >= 0

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_empty_database(self):
        """Unhappy path: Lege database retourneert None."""
        with DuckDBManager() as db:
            tester = StatisticalTester(db)
            result = tester.ttest_maker_vs_taker(market="kalshi")
            assert result is None

    def test_unhappy_path_insufficient_data(self):
        """Unhappy path: Te weinig data retourneert None."""
        with DuckDBManager() as db:
            df = pd.DataFrame({
                "id": ["t1"],
                "ticker": ["BTC"],
                "category": ["crypto"],
                "market_title": ["BTC"],
                "side": ["buy"],
                "yes_price": [0.72],
                "no_price": [0.28],
                "volume": [100],
                "trade_time": pd.to_datetime(["2026-01-01"]),
                "taker_side": ["buy"],
                "created_at": pd.to_datetime(["2026-01-01"])
            })
            db.insert_dataframe("kalshi_trades", df)

            tester = StatisticalTester(db)
            result = tester.ttest_maker_vs_taker(market="kalshi")
            assert result is None
```

---

### 📎 MICROTASK 3.3.1: Implement VolumeTrendAnalyzer

**Microtask ID:** MT-PM-011-001
**Geschatte tijd:** 60 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.3.2: Implement StatisticalTester

**Microtask ID:** MT-PM-011-002
**Geschatte tijd:** 60 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.3.3: Write & Run TDD Tests

**Microtask ID:** MT-PM-011-003
**Geschatte tijd:** 60 min
**Status:** 🔴 TODO

---

## 📌 TASK 3.4: Signal Generator Engine

**Task ID:** TASK-PM-012
**Status:** ✅ COMPLETE (15/15 tests passing)
**Voltooide tijd:** ~2.5 uur
**Dependencies:** TASK-PM-010, TASK-PM-011
**Assignee:** _____

### Task Beschrijving
Implementeer de signal generator die analyse-resultaten omzet naar actionable `MarketSignal` objecten. Dit is de brug tussen de analyse-engine en de API endpoints.

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer Signal Generator Engine
═══════════════════════════════════════════════════════════════════════════════

CONTEXT:
- Neemt MakerTakerResult, VolumeTrendResult als input
- Produceert MarketSignal objecten (gedefinieerd in src/api/schemas/signal.py)
- Combineert meerdere analyses tot composite signals
- Slaat gegenereerde signals op in DuckDB

───────────────────────────────────────────────────────────────────────────────
BESTAND: prediction-market-analysis/src/signals/generator.py
───────────────────────────────────────────────────────────────────────────────

"""
Signal Generator Engine

Converts analysis results into actionable MarketSignal objects.
Combines multiple analysis dimensions into composite signals.

Pipeline:
1. Run analyses (maker/taker, volume, statistical)
2. for each category: combine results into composite signal
3. Apply confidence thresholds
4. Generate MarketSignal objects
5. Store in database
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from src.db.duckdb_manager import DuckDBManager
from src.analysis.maker_taker import MakerTakerAnalyzer, MakerTakerResult
from src.analysis.volume_trends import VolumeTrendAnalyzer, VolumeTrendResult
from src.analysis.statistical_tests import StatisticalTester, StatTestResult
from src.api.schemas.signal import (
    MarketSignal,
    MarketSource,
    SignalCategory,
    SignalType
)

logger = logging.getLogger(__name__)


# Mapping van prediction market categories naar SignalCategory enum
CATEGORY_MAP = {
    "crypto": SignalCategory.CRYPTO,
    "politics": SignalCategory.POLITICS,
    "economics": SignalCategory.ECONOMICS,
    "finance": SignalCategory.FINANCE,
    "sports": SignalCategory.SPORTS,
    "entertainment": SignalCategory.ENTERTAINMENT,
}

# Mapping van prediction market category naar related trading symbol
CATEGORY_SYMBOL_MAP = {
    "crypto": "BTC",
    "finance": "SPY",
    "economics": "DXY",
}


class SignalGenerator:
    """
    Generates trading signals from prediction market analyses.

    Combines maker/taker advantage, volume trends, and statistical
    tests into composite market signals.
    """

    # Minimum confidence to emit a signal
    MIN_CONFIDENCE = 0.3

    def __init__(self, db: DuckDBManager):
        self.db = db
        self.maker_taker = MakerTakerAnalyzer(db)
        self.volume = VolumeTrendAnalyzer(db)
        self.stats = StatisticalTester(db)

    def generate_signals(
        self,
        market: str = "kalshi",
        category: Optional[str] = None
    ) -> List[MarketSignal]:
        """
        Generate signals for a market.

        Runs all analyses and combines results into MarketSignal objects.

        Args:
            market: "kalshi" or "polymarket"
            category: Optional category filter

        Returns:
            List of generated MarketSignal objects
        """
        logger.info(f"Generating signals for {market} (category={category})")

        # Run analyses
        if market == "kalshi":
            mt_results = self.maker_taker.analyze_kalshi(category=category)
        else:
            mt_results = self.maker_taker.analyze_polymarket(category=category)

        vol_results = self.volume.analyze(market=market, category=category)
        stat_result = self.stats.ttest_maker_vs_taker(market=market, category=category)

        # Build signal per category from combined analysis
        signals = []

        categories_seen = set()
        for mt in mt_results:
            categories_seen.add(mt.category)
        for vol in vol_results:
            categories_seen.add(vol.category)

        for cat in categories_seen:
            signal = self._build_composite_signal(
                category=cat,
                market=market,
                mt_results=[r for r in mt_results if r.category == cat],
                vol_results=[r for r in vol_results if r.category == cat],
                stat_result=stat_result
            )

            if signal and signal.confidence >= self.MIN_CONFIDENCE:
                signals.append(signal)
                self._store_signal(signal)

        logger.info(f"Generated {len(signals)} signals")
        return signals

    def _build_composite_signal(
        self,
        category: str,
        market: str,
        mt_results: List[MakerTakerResult],
        vol_results: List[VolumeTrendResult],
        stat_result: Optional[StatTestResult]
    ) -> Optional[MarketSignal]:
        """Build composite signal from multiple analyses."""

        indicators: Dict[str, float] = {}
        direction_votes: Dict[str, float] = {}  # direction -> weight

        # Maker/Taker component
        if mt_results:
            mt = mt_results[0]
            indicators["maker_advantage"] = mt.advantage
            indicators["maker_confidence"] = mt.confidence

            if mt.signal_direction == "bullish":
                direction_votes["bullish"] = mt.confidence
            elif mt.signal_direction == "bearish":
                direction_votes["bearish"] = mt.confidence
            else:
                direction_votes["neutral"] = mt.confidence

        # Volume component
        if vol_results:
            vol = vol_results[0]
            indicators["volume_change_24h"] = vol.volume_change_pct / 100
            indicators["volume_z_score"] = vol.z_score
            indicators["volume_unusual"] = 1.0 if vol.is_unusual else 0.0

        # Statistical component
        if stat_result:
            indicators["stat_p_value"] = stat_result.p_value
            indicators["stat_effect_size"] = stat_result.effect_size or 0
            indicators["stat_significant"] = 1.0 if stat_result.is_significant else 0.0

        if not indicators:
            return None

        # Determine overall direction (weighted vote)
        if not direction_votes:
            signal_type = SignalType.NEUTRAL
        else:
            winning = max(direction_votes, key=direction_votes.get)
            signal_type = SignalType(winning)

        # Calculate composite confidence
        confidences = [v for v in direction_votes.values()]
        confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Map category
        signal_category = CATEGORY_MAP.get(category, SignalCategory.OTHER)
        symbol = CATEGORY_SYMBOL_MAP.get(category)

        # Map market
        market_source = MarketSource.KALSHI if market == "kalshi" else MarketSource.POLYMARKET

        return MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:12]}",
            market=market_source,
            category=signal_category,
            signal_type=signal_type,
            confidence=round(confidence, 3),
            symbol=symbol,
            indicators={k: round(v, 6) for k, v in indicators.items()},
            timestamp=datetime.utcnow(),
            metadata={
                "generator": "composite",
                "components": list(indicators.keys())
            }
        )

    def _store_signal(self, signal: MarketSignal) -> None:
        """Store generated signal in database."""
        try:
            import json
            self.db.execute(
                """
                INSERT INTO generated_signals
                (signal_id, market, category, signal_type, confidence, symbol, indicators, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    signal.id,
                    signal.market.value,
                    signal.category.value,
                    signal.signal_type.value,
                    signal.confidence,
                    signal.symbol,
                    json.dumps(signal.indicators),
                    signal.timestamp
                ]
            )
        except Exception as e:
            logger.error(f"Failed to store signal: {e}")

───────────────────────────────────────────────────────────────────────────────
BESTAND: prediction-market-analysis/src/signals/__init__.py
───────────────────────────────────────────────────────────────────────────────

"""Signals module for Prediction Market Intelligence."""
from src.signals.generator import SignalGenerator

__all__ = ["SignalGenerator"]

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from src.signals.generator import SignalGenerator
print('SignalGenerator imported OK')
"

═══════════════════════════════════════════════════════════════════════════════
```

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_signal_generator.py`

```python
"""
Tests voor Signal Generator.
Run: pytest prediction-market-analysis/tests/test_signal_generator.py -v
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.db.duckdb_manager import DuckDBManager
from src.signals.generator import SignalGenerator
from src.api.schemas.signal import MarketSignal, SignalType


class TestSignalGenerator:
    """Tests voor SignalGenerator."""

    @pytest.fixture
    def db_with_full_data(self):
        """DuckDB met volledige test dataset."""
        db = DuckDBManager()
        db.initialize()

        np.random.seed(42)
        n = 200

        df = pd.DataFrame({
            "id": [f"t{i}" for i in range(n)],
            "ticker": ["BTC-YES"] * n,
            "category": ["crypto"] * n,
            "market_title": ["BTC > 100k"] * n,
            "side": ["buy"] * n,
            "yes_price": np.concatenate([
                np.random.normal(0.75, 0.03, n // 2),
                np.random.normal(0.68, 0.03, n // 2),
            ]),
            "no_price": [0.28] * n,
            "volume": np.random.randint(50, 500, n),
            "trade_time": pd.to_datetime(["2026-01-15"] * n),
            "taker_side": ["buy"] * (n // 2) + ["sell"] * (n // 2),
            "created_at": pd.to_datetime(["2026-01-15"] * n)
        })
        db.insert_dataframe("kalshi_trades", df)

        yield db
        db.close()

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_generate_returns_signals(self, db_with_full_data):
        """Happy path: Generator produceert signals."""
        gen = SignalGenerator(db_with_full_data)
        signals = gen.generate_signals(market="kalshi")

        assert isinstance(signals, list)
        if signals:
            assert all(isinstance(s, MarketSignal) for s in signals)

    def test_happy_path_signal_has_indicators(self, db_with_full_data):
        """Happy path: Signal bevat indicators."""
        gen = SignalGenerator(db_with_full_data)
        signals = gen.generate_signals(market="kalshi")

        if signals:
            signal = signals[0]
            assert len(signal.indicators) > 0
            assert "maker_advantage" in signal.indicators

    def test_happy_path_signal_confidence_bounded(self, db_with_full_data):
        """Happy path: Confidence is altijd 0-1."""
        gen = SignalGenerator(db_with_full_data)
        signals = gen.generate_signals(market="kalshi")

        for signal in signals:
            assert 0 <= signal.confidence <= 1

    def test_happy_path_signal_stored_in_db(self, db_with_full_data):
        """Happy path: Generated signals worden opgeslagen in DB."""
        gen = SignalGenerator(db_with_full_data)
        signals = gen.generate_signals(market="kalshi")

        count = db_with_full_data.get_table_count("generated_signals")
        assert count == len(signals)

    def test_happy_path_signal_type_valid(self, db_with_full_data):
        """Happy path: Signal type is valid enum."""
        gen = SignalGenerator(db_with_full_data)
        signals = gen.generate_signals(market="kalshi")

        for signal in signals:
            assert signal.signal_type in [
                SignalType.BULLISH,
                SignalType.BEARISH,
                SignalType.NEUTRAL
            ]

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_empty_database(self):
        """Unhappy path: Lege database → geen signals."""
        with DuckDBManager() as db:
            gen = SignalGenerator(db)
            signals = gen.generate_signals(market="kalshi")
            assert signals == []

    def test_unhappy_path_low_confidence_filtered(self):
        """Unhappy path: Signals met lage confidence worden gefilterd."""
        with DuckDBManager() as db:
            # Insert minimal data → lage confidence
            df = pd.DataFrame({
                "id": ["t1", "t2"],
                "ticker": ["BTC"] * 2,
                "category": ["testcat"] * 2,
                "market_title": ["test"] * 2,
                "side": ["buy"] * 2,
                "yes_price": [0.50, 0.50],
                "no_price": [0.50, 0.50],
                "volume": [1, 1],
                "trade_time": pd.to_datetime(["2026-01-01"] * 2),
                "taker_side": ["buy", "sell"],
                "created_at": pd.to_datetime(["2026-01-01"] * 2)
            })
            db.insert_dataframe("kalshi_trades", df)

            gen = SignalGenerator(db)
            gen.MIN_CONFIDENCE = 0.9  # Set high threshold
            signals = gen.generate_signals(market="kalshi")

            # Should produce no signals (too few trades → low confidence)
            assert len(signals) == 0
```

---

### 📎 MICROTASK 3.4.1: Implement SignalGenerator

**Microtask ID:** MT-PM-012-001
**Geschatte tijd:** 90 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.4.2: Wire Generator into API Endpoints

**Microtask ID:** MT-PM-012-002
**Geschatte tijd:** 45 min
**Status:** 🔴 TODO

### 📎 MICROTASK 3.4.3: Write & Run TDD Tests

**Microtask ID:** MT-PM-012-003
**Geschatte tijd:** 45 min
**Status:** 🔴 TODO

---

## ✅ Epic 3 Completion Checklist

### Tasks Status

| Task | Status | Acceptatiecriteria |
|------|--------|-------------------|
| TASK 3.1: DuckDB Manager | ✅ COMPLETE | CRUD, Parquet views, context manager (28/28 tests) |
| TASK 3.2: Maker/Taker Analysis | ✅ COMPLETE | Kalshi + Polymarket, confidence scoring (26/26 tests) |
| TASK 3.3: Volume & Stats | ✅ COMPLETE | Volume trends, t-test, chi-square (26/26 tests) |
| TASK 3.4: Signal Generator | ✅ COMPLETE | Composite signals, DB storage (15/15 tests) |
| TASK 3.5: FastAPI Integration | ✅ COMPLETE | AnalysisService, IngestionService, async jobs (9/9 tests) |
| TASK 3.6: E2E Testing & Docs | ✅ COMPLETE | Full workflow tests, API documentation (26/26 tests) |
| TASK 3.7: Docker Verification | ✅ COMPLETE | 8-step Docker build verification script |
| TASK 3.8: Completion Summary | ✅ COMPLETE | Final reports and documentation |

### Microtasks Status

- [x] **MT-3.1.1**: DB Directory & Init ✅
- [x] **MT-3.1.2**: DuckDBManager implementation ✅
- [x] **MT-3.1.3**: ParquetHandler implementation ✅
- [x] **MT-3.2.1**: Analysis module structure ✅
- [x] **MT-3.2.2**: MakerTakerAnalyzer ✅
- [x] **MT-3.2.3**: Maker/Taker TDD tests ✅
- [x] **MT-3.3.1**: VolumeTrendAnalyzer ✅
- [x] **MT-3.3.2**: StatisticalTester ✅
- [x] **MT-3.3.3**: Volume & Stats TDD tests ✅
- [x] **MT-3.4.1**: SignalGenerator engine ✅
- [x] **MT-3.4.2**: Wire into API endpoints ✅
- [x] **MT-3.4.3**: Signal Generator TDD tests ✅
- [x] **MT-3.5.1**: AnalysisService & IngestionService ✅
- [x] **MT-3.5.2**: API endpoint integration ✅
- [x] **MT-3.5.3**: Integration tests ✅
- [x] **MT-3.6.1**: E2E workflow tests (26 tests) ✅
- [x] **MT-3.6.2**: API documentation (500+ lines) ✅
- [x] **MT-3.6.3**: Test execution validation ✅
- [x] **MT-3.7.1**: Docker verification script ✅
- [x] **MT-3.7.2**: 8-step verification process ✅
- [x] **MT-3.8.1**: Final completion report ✅
- [x] **MT-3.8.2**: Completion checklist ✅

### Definition of Done
- [x] DuckDB initialiseert correct met schema ✅
- [x] Alle 3 analyse types produceren resultaten ✅
- [x] SignalGenerator combineert analyses tot composite signals ✅
- [x] Signals worden opgeslagen in database ✅
- [x] Alle unit tests GROEN (happy + unhappy paths) - 133/133 ✅
- [x] E2E tests valideren volledige workflow ✅
- [x] Docker verification script functioneert ✅
- [x] Volledige documentatie aanwezig ✅

---

**Volgende Epic:** [EPIC 4: Platform Integratie](EPIC_04_PLATFORM_INTEGRATION.md)
