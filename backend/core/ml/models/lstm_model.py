"""
LSTM Model for Chitta Forecasting
"""

import logging

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


class ChittaLSTM(nn.Module):
    """LSTM model voor het voorspellen van toekomstige markt returns."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super(ChittaLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        # Fully connected output layer
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: [batch_size, sequence_length, input_size]

        Returns:
            [batch_size, output_size]
        """
        # LSTM forward
        lstm_out, (hidden, cell) = self.lstm(x)

        # Gebruik laatste hidden state
        last_hidden = lstm_out[:, -1, :]

        # FC layers
        output = self.fc(last_hidden)

        return output


class ModelTrainer:
    """Trainer voor LSTM/Transformer modellen."""

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 0.001,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.model = model.to(device)
        self.device = device
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        logger.info(f"Model trainer initialized on {device}")

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Train één epoch."""
        self.model.train()
        total_loss = 0

        for batch_idx, (sequences, labels) in enumerate(dataloader):
            sequences = sequences.to(self.device)
            labels = labels.to(self.device)

            # Forward
            self.optimizer.zero_grad()
            predictions = self.model(sequences).squeeze()
            loss = self.criterion(predictions, labels)

            # Backward
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(dataloader)

    def validate(self, dataloader: DataLoader) -> tuple[float, float]:
        """Validate model."""
        self.model.eval()
        total_loss = 0
        correct_direction = 0
        total = 0

        with torch.no_grad():
            for sequences, labels in dataloader:
                sequences = sequences.to(self.device)
                labels = labels.to(self.device)

                predictions = self.model(sequences).squeeze()
                loss = self.criterion(predictions, labels)
                total_loss += loss.item()

                # Direction accuracy
                pred_sign = torch.sign(predictions)
                true_sign = torch.sign(labels)
                correct_direction += (pred_sign == true_sign).sum().item()
                total += len(labels)

        avg_loss = total_loss / len(dataloader)
        direction_acc = correct_direction / total if total > 0 else 0

        return avg_loss, direction_acc

    def save_model(self, path: str):
        """Sla model op."""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            path,
        )
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Laad model."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        logger.info(f"Model loaded from {path}")
