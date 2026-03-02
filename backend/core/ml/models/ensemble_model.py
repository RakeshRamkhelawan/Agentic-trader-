"""
Ensemble Model - Combineert LSTM en Transformer

Voordelen:
- Diversiteit in voorspellingen
- Robuuster tegen overfitting
- Betere generalisatie
"""

import logging

import torch
import torch.nn as nn

from .lstm_model import ChittaLSTM
from .transformer_model import ChittaTransformer

logger = logging.getLogger(__name__)


class ChittaEnsemble(nn.Module):
    """
    Ensemble van LSTM en Transformer modellen.

    Architecture:
    - LSTM branch: captures sequential patterns
    - Transformer branch: captures long-range dependencies
    - Meta-learner: learns optimal combination
    """

    def __init__(
        self,
        input_size: int,
        lstm_hidden: int = 128,
        lstm_layers: int = 2,
        transformer_d_model: int = 128,
        transformer_layers: int = 4,
        transformer_heads: int = 8,
        dropout: float = 0.2,
        output_size: int = 1,
        ensemble_method: str = "weighted"  # "weighted", "average", "meta"
    ):
        super(ChittaEnsemble, self).__init__()

        self.ensemble_method = ensemble_method

        # LSTM branch
        self.lstm = ChittaLSTM(
            input_size=input_size,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            output_size=output_size,
            dropout=dropout
        )

        # Transformer branch
        self.transformer = ChittaTransformer(
            input_size=input_size,
            d_model=transformer_d_model,
            nhead=transformer_heads,
            num_layers=transformer_layers,
            output_size=output_size,
            dropout=dropout
        )

        # Ensemble weights (learnable indien weighted)
        if ensemble_method == "weighted":
            self.lstm_weight = nn.Parameter(torch.tensor(0.5))
            self.transformer_weight = nn.Parameter(torch.tensor(0.5))
        elif ensemble_method == "meta":
            # Meta-learner die beide outputs combineert
            self.meta_learner = nn.Sequential(
                nn.Linear(output_size * 2, 32),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(32, output_size)
            )

        logger.info(f"ChittaEnsemble initialized: method={ensemble_method}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass door beide modellen + ensemble.

        Args:
            x: [batch, seq, features]

        Returns:
            [batch, output_size]
        """
        # Get predictions from both models
        lstm_pred = self.lstm(x)
        transformer_pred = self.transformer(x)

        # Combine
        if self.ensemble_method == "average":
            # Simple average
            output = (lstm_pred + transformer_pred) / 2

        elif self.ensemble_method == "weighted":
            # Learnable weighted average
            # Softmax zorgt dat weights sum to 1
            weights = torch.softmax(
                torch.stack([self.lstm_weight, self.transformer_weight]),
                dim=0
            )
            output = weights[0] * lstm_pred + weights[1] * transformer_pred

        elif self.ensemble_method == "meta":
            # Meta-learner
            combined = torch.cat([lstm_pred, transformer_pred], dim=-1)
            output = self.meta_learner(combined)

        else:
            raise ValueError(f"Unknown ensemble method: {self.ensemble_method}")

        return output

    def get_model_weights(self) -> dict:
        """Get current ensemble weights."""
        if self.ensemble_method == "weighted":
            weights = torch.softmax(
                torch.stack([self.lstm_weight, self.transformer_weight]),
                dim=0
            )
            return {
                "lstm": weights[0].item(),
                "transformer": weights[1].item()
            }
        return {"method": self.ensemble_method}


class StackingEnsemble(nn.Module):
    """
    Stacking ensemble met multiple base models.

    Train meerdere modellen op verschillende subsets van data,
    combineer met meta-learner.
    """

    def __init__(
        self,
        input_size: int,
        n_models: int = 3,
        hidden_size: int = 128,
        dropout: float = 0.2
    ):
        super().__init__()

        self.n_models = n_models

        # Create diverse base models
        self.models = nn.ModuleList([
            ChittaLSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=2 + i,  # Different depths
                dropout=dropout,
                output_size=1
            )
            for i in range(n_models)
        ])

        # Meta-learner
        self.meta = nn.Sequential(
            nn.Linear(n_models, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1)
        )

    def forward(self, x):
        # Get predictions from all models
        predictions = [model(x) for model in self.models]
        stacked = torch.cat(predictions, dim=-1)

        # Meta-learner combineert
        return self.meta(stacked)

    def predict_with_uncertainty(self, x, n_samples: int = 10):
        """
        Predict met uncertainty estimation via Monte Carlo dropout.
        """
        self.train()  # Enable dropout

        predictions = []
        for _ in range(n_samples):
            with torch.no_grad():
                pred = self.forward(x)
                predictions.append(pred)

        self.eval()

        # Calculate mean and uncertainty
        predictions = torch.stack(predictions)
        mean = predictions.mean(dim=0)
        uncertainty = predictions.std(dim=0)

        return mean, uncertainty
