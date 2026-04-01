import pytest

from backend.core.symbol_normalizer import SymbolNormalizer


class TestSymbolNormalizer:
    """Tests for the SymbolNormalizer class."""

    def test_to_canonical_dash(self):
        """to_canonical("BTC-EUR") should return "BTC/EUR"."""
        assert SymbolNormalizer.to_canonical("BTC-EUR") == "BTC/EUR"

    def test_to_canonical_slash_idempotent(self):
        """to_canonical("BTC/EUR") should return "BTC/EUR" (idempotent)."""
        assert SymbolNormalizer.to_canonical("BTC/EUR") == "BTC/EUR"

    def test_to_canonical_concatenated(self):
        """to_canonical("BTCEUR") should return "BTC/EUR" (concatenated with known quote currencies)."""
        # Testing with EUR as it is a common quote currency mentioned in the prompt
        assert SymbolNormalizer.to_canonical("BTCEUR") == "BTC/EUR"

    def test_to_canonical_case_insensitive(self):
        """to_canonical("btc-eur") should return "BTC/EUR" (case insensitive)."""
        assert SymbolNormalizer.to_canonical("btc-eur") == "BTC/EUR"

    def test_to_display_canonical(self):
        """to_display("BTC/EUR") should return "BTC-EUR"."""
        assert SymbolNormalizer.to_display("BTC/EUR") == "BTC-EUR"

    def test_to_display_dash_idempotent(self):
        """to_display("BTC-EUR") should return "BTC-EUR" (idempotent)."""
        assert SymbolNormalizer.to_display("BTC-EUR") == "BTC-EUR"

    def test_to_exchange_revolut(self):
        """to_exchange("BTC/EUR", "revolut") should return "BTC-EUR"."""
        assert SymbolNormalizer.to_exchange("BTC/EUR", "revolut") == "BTC-EUR"

    def test_to_exchange_bitvavo(self):
        """to_exchange("BTC/EUR", "bitvavo") should return "BTC/EUR"."""
        assert SymbolNormalizer.to_exchange("BTC/EUR", "bitvavo") == "BTC/EUR"

    def test_to_exchange_binance(self):
        """to_exchange("BTC/EUR", "binance") should return "BTC/EUR"."""
        assert SymbolNormalizer.to_exchange("BTC/EUR", "binance") == "BTC/EUR"

    def test_from_exchange_revolut(self):
        """from_exchange("BTC-EUR", "revolut") should return "BTC/EUR"."""
        assert SymbolNormalizer.from_exchange("BTC-EUR", "revolut") == "BTC/EUR"

    def test_from_exchange_bitvavo(self):
        """from_exchange("BTC/EUR", "bitvavo") should return "BTC/EUR"."""
        assert SymbolNormalizer.from_exchange("BTC/EUR", "bitvavo") == "BTC/EUR"

    # Unhappy Path Tests

    def test_to_canonical_empty_string(self):
        """to_canonical("") should raise ValueError."""
        with pytest.raises(ValueError):
            SymbolNormalizer.to_canonical("")

    def test_to_canonical_no_quote(self):
        """to_canonical("BTC") should raise ValueError (no quote currency)."""
        with pytest.raises(ValueError):
            SymbolNormalizer.to_canonical("BTC")

    def test_to_canonical_invalid(self):
        """to_canonical("INVALID") should raise ValueError."""
        with pytest.raises(ValueError):
            SymbolNormalizer.to_canonical("INVALID")

    def test_to_exchange_unknown(self):
        """to_exchange("BTC/EUR", "unknown_exchange") should raise ValueError or fallback."""
        # Requirement says: moet ValueError raisen of fallback naar canoniek.
        # Given the TDD context, we assume ValueError for strictness unless implementation decides otherwise.
        with pytest.raises(ValueError):
            SymbolNormalizer.to_exchange("BTC/EUR", "unknown_exchange")

    def test_to_canonical_none(self):
        """to_canonical(None) should raise TypeError."""
        with pytest.raises(TypeError):
            SymbolNormalizer.to_canonical(None)

    def test_to_canonical_too_many_segments(self):
        """to_canonical("BTC/EUR/EXTRA") should raise ValueError."""
        with pytest.raises(ValueError):
            SymbolNormalizer.to_canonical("BTC/EUR/EXTRA")

    def test_to_canonical_whitespace(self):
        """to_canonical(" BTC/EUR ") should return "BTC/EUR" (trimmed)."""
        assert SymbolNormalizer.to_canonical(" BTC/EUR ") == "BTC/EUR"
