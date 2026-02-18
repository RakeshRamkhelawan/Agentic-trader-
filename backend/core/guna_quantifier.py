from typing import Dict

from backend.schemas.guna import GunaVector


class GunaQuantifier:
    """
    Kwantificeert de Guna-vibratie van inkomende data (tekst, numeriek).
    """

    def __init__(self):
        # Initialiseer hier eventuele NLP modellen of drempelwaarden
        pass

    def quantify_text(self, text: str) -> GunaVector:
        """
        Kwantificeert de Guna-compositie van een tekst.
        Heuristiek (voorlopig):
        - Rajas: woorden die actie, beweging, verandering suggereren.
        - Tamas: woorden die stagnatie, chaos, negatieve emotie suggereren.
        - Sattva: neutrale, feitelijke woorden, evenwicht.
        """
        if not text:
            return GunaVector(sattva=1 / 3, rajas=1 / 3, tamas=1 / 3)  # Neutraal

        text_lower = text.lower()

        # Rajas indicatoren
        rajas_score = 0
        rajas_keywords = [
            "surges",
            "jumps",
            "rises",
            "falls",
            "breakout",
            "action",
            "volatility",
            "movement",
            "change",
            "momentum",
            "buy",
            "sell",
            "urgent",
            "breaking",
        ]
        for kw in rajas_keywords:
            rajas_score += text_lower.count(kw)

        # Tamas indicatoren
        tamas_score = 0
        tamas_keywords = [
            "crash",
            "fear",
            "panic",
            "collapse",
            "stagnant",
            "bear",
            "crisis",
            "tension",
            "uncertainty",
            "frozen",
            "resist",
            "chaos",
        ]
        for kw in tamas_keywords:
            tamas_score += text_lower.count(kw)

        # Sattva indicatoren (als tegenhanger of neutraal)
        sattva_score = 0
        sattva_keywords = [
            "stable",
            "growth",
            "predictable",
            "healthy",
            "balanced",
            "calm",
            "objective",
            "factual",
            "clear",
        ]
        for kw in sattva_keywords:
            sattva_score += text_lower.count(kw)

        # Voeg een bias toe. Teksten zijn zelden perfect neutraal.
        # De sum van keywords kan variëren. Normaliseer naar een 0-1 range

        # Simpele normalisatie en bias
        total_score = rajas_score + tamas_score + sattva_score

        if total_score == 0:  # Geen keywords gevonden
            return GunaVector(sattva=1 / 3, rajas=1 / 3, tamas=1 / 3)

        rajas_norm = rajas_score / total_score
        tamas_norm = tamas_score / total_score
        sattva_norm = sattva_score / total_score

        # Simpele aanpassing voor "feitelijkheid" (hogere Sattva) als er geen sterke Rajas/Tamas zijn
        if rajas_norm < 0.1 and tamas_norm < 0.1:
            sattva_norm += 0.5  # Boost Sattva for neutral text

        # Zorg dat de som 1 is, na eventuele bias
        current_sum = sattva_norm + rajas_norm + tamas_norm
        if current_sum != 1.0:
            factor = 1.0 / current_sum
            sattva_norm *= factor
            rajas_norm *= factor
            tamas_norm *= factor

        return GunaVector(sattva=sattva_norm, rajas=rajas_norm, tamas=tamas_norm)

    def quantify_numerical_data(self, data: Dict[str, float]) -> GunaVector:
        """
        Kwantificeert de Guna-compositie van numerieke data (bijv. volatiliteit, trend).
        """
        # Voorlopige heuristiek:
        # Hoge volatiliteit -> Rajas / Tamas
        # Sterke trend -> Rajas
        # Lage volatiliteit, stabiele waarden -> Sattva

        sattva = 0.33
        rajas = 0.33
        tamas = 0.33

        volatility = data.get("volatility", 0.0)
        trend_strength = data.get("trend_strength", 0.0)

        if volatility > 0.05:  # High volatility
            rajas += 0.2
            tamas += 0.2
            sattva -= 0.4
        elif volatility < 0.01:  # Low volatility
            sattva += 0.2
            rajas -= 0.1
            tamas -= 0.1

        if trend_strength > 0.5:  # Strong trend
            rajas += 0.2
            sattva -= 0.1
            tamas -= 0.1
        elif trend_strength < -0.5:  # Strong reverse trend (also Rajas)
            rajas += 0.2
            sattva -= 0.1
            tamas -= 0.1

        # Normaliseer naar 1.0
        total = sattva + rajas + tamas
        sattva /= total
        rajas /= total
        tamas /= total

        return GunaVector(sattva=sattva, rajas=rajas, tamas=tamas)
