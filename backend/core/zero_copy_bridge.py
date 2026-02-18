import logging
import time
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TradingIntent:
    """
    Python representation of the intent struct.
    """

    action: int  # -1=sell, 0=hold, 1=buy
    size: float
    confidence: float
    stop_loss: float
    take_profit: float
    max_hold_ms: int
    entry_price: float
    timestamp_ns: int


class ZeroCopyBridge:
    """
    Manages shared memory for high-frequency communication between
    Cognitive Mind (Writer) and Reflex Body (Reader).
    """

    # Define the structured array dtype matching the C layout
    # Aligned to 64 bytes (cache line friendly)
    INTENT_DTYPE = np.dtype(
        [
            ("action", "i1"),  # 1 byte
            ("size", "f4"),  # 4 bytes
            ("confidence", "f4"),  # 4 bytes
            ("stop_loss", "f4"),  # 4 bytes
            ("take_profit", "f4"),  # 4 bytes
            ("max_hold_ms", "i4"),  # 4 bytes
            ("entry_price", "f4"),  # 4 bytes
            ("timestamp_ns", "i8"),  # 8 bytes
            ("padding", "V31"),  # 31 bytes padding to reach 64 bytes
        ]
    )

    # Default SHM names
    MARKET_DATA_NAME = "market_data_v2"
    TRADING_INTENTS_NAME = "trading_intents_v2"

    # Market Data structure (Aligned to 64 bytes)
    MARKET_DATA_DTYPE = np.dtype(
        [
            ("bid_price", "f8"),  # 8 bytes
            ("bid_size", "f8"),  # 8 bytes
            ("ask_price", "f8"),  # 8 bytes
            ("ask_size", "f8"),  # 8 bytes
            ("last_price", "f8"),  # 8 bytes
            ("timestamp_ns", "i8"),  # 8 bytes
            ("padding", "V16"),  # 16 bytes padding to reach 64 bytes
        ]
    )

    def __init__(
        self,
        max_symbols: int = 100,
        create: bool = False,
        shm_name: str = "trading_intents_v2",
        dtype_name: str = "intent",
    ):
        self.max_symbols = max_symbols
        self.shm_name = shm_name
        self.dtype_name = dtype_name
        self.shm: Optional[shared_memory.SharedMemory] = None
        self.data_array: Optional[
            np.ndarray
        ] = None  # Renamed from intents to generic data_array
        self._is_creator = create

        # Select DTYPE based on name
        if dtype_name == "market":
            self.dtype = self.MARKET_DATA_DTYPE
        else:
            self.dtype = self.INTENT_DTYPE

        try:
            if create:
                try:
                    self.shm = shared_memory.SharedMemory(
                        name=self.shm_name,
                        create=True,
                        size=max_symbols * self.dtype.itemsize,
                    )
                    logger.info(
                        f"Created shared memory '{self.shm_name}' size={self.shm.size} dtype={dtype_name}"
                    )

                    # Initialize with zeros
                    self.data_array = np.ndarray(
                        (max_symbols,), dtype=self.dtype, buffer=self.shm.buf
                    )
                    # Use byte view to zero out memory (handles padding correctly)
                    # self.data_array.view(np.uint8).fill(0)
                    # Optimization: Just fill with 0
                    self.shm.buf[: self.shm.size] = bytes(self.shm.size)

                except FileExistsError:
                    logger.warning(
                        f"Shared memory '{self.shm_name}' already exists. Attaching..."
                    )
                    self.shm = shared_memory.SharedMemory(name=self.shm_name)
                    self._is_creator = False
            else:
                self.shm = shared_memory.SharedMemory(name=self.shm_name)
                logger.info(f"Attached to shared memory '{self.shm_name}'")

            if self.data_array is None:
                self.data_array = np.ndarray(
                    (max_symbols,), dtype=self.dtype, buffer=self.shm.buf
                )

        except Exception as e:
            logger.error(f"Failed to initialize ZeroCopyBridge: {e}")
            raise

    def close(self):
        """Close access to shared memory."""
        if self.shm:
            self.shm.close()
            if self._is_creator:
                try:
                    self.shm.unlink()
                    logger.info(f"Unlinked shared memory '{self.shm_name}'")
                except FileNotFoundError:
                    pass

    def _get_idx(self, symbol: str) -> int:
        """Simple hash-based indexing for prototype."""
        return hash(symbol) % self.max_symbols

    def write_intent(self, symbol: str, intent: TradingIntent):
        """
        Write trading intent to shared memory.
        """
        if self.data_array is None or self.dtype_name != "intent":
            return

        idx = self._get_idx(symbol)

        self.data_array[idx]["action"] = intent.action
        self.data_array[idx]["size"] = intent.size
        self.data_array[idx]["confidence"] = intent.confidence
        self.data_array[idx]["stop_loss"] = intent.stop_loss
        self.data_array[idx]["take_profit"] = intent.take_profit
        self.data_array[idx]["max_hold_ms"] = intent.max_hold_ms
        self.data_array[idx]["entry_price"] = intent.entry_price
        self.data_array[idx]["timestamp_ns"] = time.time_ns()

    def read_intent(self, symbol: str) -> Optional[TradingIntent]:
        """
        Read trading intent from shared memory.
        """
        if self.data_array is None or self.dtype_name != "intent":
            return None

        idx = self._get_idx(symbol)
        row = self.data_array[idx]

        if row["timestamp_ns"] == 0:
            return None

        return TradingIntent(
            action=int(row["action"]),
            size=float(row["size"]),
            confidence=float(row["confidence"]),
            stop_loss=float(row["stop_loss"]),
            take_profit=float(row["take_profit"]),
            max_hold_ms=int(row["max_hold_ms"]),
            entry_price=float(row["entry_price"]),
            timestamp_ns=int(row["timestamp_ns"]),
        )

    def write_market_data(
        self,
        symbol: str,
        bid: float,
        ask: float,
        last: float,
        bid_size: float = 0.0,
        ask_size: float = 0.0,
    ):
        """
        Write market data to shared memory.
        """
        if self.data_array is None or self.dtype_name != "market":
            return

        idx = self._get_idx(symbol)

        self.data_array[idx]["bid_price"] = bid
        self.data_array[idx]["bid_size"] = bid_size
        self.data_array[idx]["ask_price"] = ask
        self.data_array[idx]["ask_size"] = ask_size
        self.data_array[idx]["last_price"] = last
        self.data_array[idx]["timestamp_ns"] = time.time_ns()

    def read_market_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Read market data from shared memory.
        """
        if self.data_array is None or self.dtype_name != "market":
            return None

        idx = self._get_idx(symbol)
        row = self.data_array[idx]

        if row["timestamp_ns"] == 0:
            return None

        return {
            "bid": float(row["bid_price"]),
            "ask": float(row["ask_price"]),
            "last": float(row["last_price"]),
            "timestamp_ns": int(row["timestamp_ns"]),
        }
