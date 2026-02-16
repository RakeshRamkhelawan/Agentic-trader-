from enum import Enum
from pydantic import BaseModel

class ComplianceStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"

class ClientClassification(str, Enum):
    RETAIL = "retail"
    PROFESSIONAL = "professional"
    ELIGIBLE_COUNTERPARTY = "eligible_counterparty"

class TradeRequest(BaseModel):
    asset: str
    amount: float
    price: float
    side: str # "buy" or "sell"
    notional_value: float

class ClientProfile(BaseModel):
    classification: ClientClassification
    experience_years: int
    knowledge_score: int # 0-10
    max_loss_tolerance_pct: float
    current_drawdown_pct: float

class MiFIDGuard:
    """
    Checks for MiFID II compliance appropriateness and loss limits.
    """
    
    def check_appropriateness(self, profile: ClientProfile, trade: TradeRequest) -> ComplianceStatus:
        # Simple Suitability Rule: 
        # Retail clients need verified knowledge (score >= 7) and experience (>= 2 years) for complex crypto assets.
        if profile.classification == ClientClassification.RETAIL:
            if profile.knowledge_score < 7 or profile.experience_years < 2:
                return ComplianceStatus.BLOCK
        return ComplianceStatus.PASS

    def check_loss_limits(self, profile: ClientProfile, trade: TradeRequest) -> ComplianceStatus:
        # If current drawdown exceeds tolerance, block new risk
        if profile.current_drawdown_pct >= profile.max_loss_tolerance_pct:
            return ComplianceStatus.BLOCK
        
        # Warning threshold (e.g. 80% usage of loss limit)
        if profile.current_drawdown_pct >= (profile.max_loss_tolerance_pct * 0.8):
            return ComplianceStatus.WARN
            
        return ComplianceStatus.PASS

    def validate(self, profile: ClientProfile, trade: TradeRequest) -> ComplianceStatus:
        approp = self.check_appropriateness(profile, trade)
        if approp == ComplianceStatus.BLOCK:
            return ComplianceStatus.BLOCK
            
        loss = self.check_loss_limits(profile, trade)
        if loss == ComplianceStatus.BLOCK:
            return ComplianceStatus.BLOCK
            
        if approp == ComplianceStatus.WARN or loss == ComplianceStatus.WARN:
            return ComplianceStatus.WARN
            
        return ComplianceStatus.PASS
