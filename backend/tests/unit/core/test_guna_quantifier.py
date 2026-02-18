import pytest

from backend.core.guna_quantifier import GunaQuantifier

# --- TEXTUAL DATA TESTS ---


def test_quantify_sattvic_text():
    """Happy Path: Text die helderheid en balans uitstraalt."""
    quantifier = GunaQuantifier()
    text = "The market shows stable growth and predictable patterns, indicating a healthy economic outlook."

    guna_vector = quantifier.quantify_text(text)

    assert guna_vector.sattva > guna_vector.rajas
    assert guna_vector.sattva > guna_vector.tamas
    assert (
        pytest.approx(guna_vector.sattva + guna_vector.rajas + guna_vector.tamas) == 1.0
    )


def test_quantify_rajasic_text():
    """Happy Path: Text die actie en verandering uitstraalt."""
    quantifier = GunaQuantifier()
    text = "BREAKING NEWS: Bitcoin price surges 20% on massive trading volume. Urgent action required!"

    guna_vector = quantifier.quantify_text(text)

    assert guna_vector.rajas > guna_vector.sattva
    assert guna_vector.rajas > guna_vector.tamas
    assert (
        pytest.approx(guna_vector.sattva + guna_vector.rajas + guna_vector.tamas) == 1.0
    )


def test_quantify_tamasic_text():
    """Happy Path: Text die inertie, onduidelijkheid of chaos uitstraalt."""
    quantifier = GunaQuantifier()
    text = "Market sentiment remains extremely cautious amidst ongoing geopolitical tensions and unclear regulations. Traders are frozen."

    guna_vector = quantifier.quantify_text(text)

    assert guna_vector.tamas > guna_vector.rajas
    assert guna_vector.tamas > guna_vector.sattva
    assert (
        pytest.approx(guna_vector.sattva + guna_vector.rajas + guna_vector.tamas) == 1.0
    )


def test_quantify_empty_text():
    """Unhappy Path: Lege tekst moet neutrale GunaVector geven."""
    quantifier = GunaQuantifier()
    text = ""

    guna_vector = quantifier.quantify_text(text)

    assert guna_vector.sattva == pytest.approx(1 / 3)
    assert guna_vector.rajas == pytest.approx(1 / 3)
    assert guna_vector.tamas == pytest.approx(1 / 3)
