"""
LSTM Model voor Chitta Forecasting

Getraind op backtest data, geen live data nodig!
"""

import logging

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


class ChittaLSTM(nn.Module):
    """
    LSTM model voor het voorspellen van toekomstige markt returns
    op basis van historische Chitta state (harmony, elemental, etc).
    """

    def __init__(
        self,
        input_size: int,  # Aantal features (harmony, equity, elemental, etc)
        hidden_size: int = 128,
        num_layers: int = 2,
        output_size: int = 1,  # Future return
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
            nn.Linear(hidden_size, 64), nn.ReLU(), nn.Dropout(dropout), nn.Linear(64, output_size)
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
        last_hidden = lstm_out[:, -1, :]  # [batch, hidden_size]

        # FC layers
        output = self.fc(last_hidden)

        return output


class ChittaTransformer(nn.Module):
    """
    Transformer model als alternatief voor LSTM.
    Beter voor lange sequences en capturing long-range dependencies.
    """

    def __init__(
        self,
        input_size: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        output_size: int = 1,
        dropout: float = 0.1,
    ):
        super(ChittaTransformer, self).__init__()

        self.d_model = d_model

        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout)

        # Transformer encoder
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers=num_layers)

        # Output layer
        self.fc = nn.Sequential(
            nn.Linear(d_model, 64), nn.ReLU(), nn.Dropout(dropout), nn.Linear(64, output_size)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: [batch_size, sequence_length, input_size]
        """
        # Project input naar d_model
        x = self.input_projection(x)  # [batch, seq, d_model]

        # Add positional encoding
        x = self.pos_encoder(x)

        # Transformer encoding
        encoded = self.transformer_encoder(x)  # [batch, seq, d_model]

        # Gebruik gemiddelde van alle time steps (kan ook laatste gebruiken)
        pooled = encoded.mean(dim=1)  # [batch, d_model]

        # Output
        output = self.fc(pooled)

        return output


class PositionalEncoding(nn.Module):
    """Positional encoding voor Transformer."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Pre-compute positional encodings
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


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

                # Direction accuracy (voor returns)
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


def train_on_backtest_data(
    backtest_dir: str = "backtest_results",
    model_type: str = "lstm",  # "lstm" of "transformer"
    epochs: int = 50,
    batch_size: int = 32,
) -> nn.Module:
    """
    Hoofdfunctie: Train een model op backtest data.

    Usage:
        model = train_on_backtest_data()
        # Model is nu getraind op je historische data!
    """
    from backend.core.ml.backtest_dataset_builder import BacktestDatasetBuilder

    # Bouw dataset
    builder = BacktestDatasetBuilder()
    dataset = builder.build_lstm_dataset(
        backtest_dir=backtest_dir, sequence_length=50, prediction_horizon=10
    )

    if len(dataset) == 0:
        raise ValueError("Geen training data gegenereerd uit backtests")

    # Split train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    # Bepaal input size van data
    sample_seq, _ = dataset[0]
    input_size = sample_seq.shape[1]  # Aantal features

    # Initialiseer model
    if model_type == "lstm":
        model = ChittaLSTM(input_size=input_size, hidden_size=128, num_layers=2)
    else:
        model = ChittaTransformer(input_size=input_size, d_model=128, num_layers=4)

    # Train
    trainer = ModelTrainer(model)

    best_val_loss = float("inf")
    for epoch in range(epochs):
        train_loss = trainer.train_epoch(train_loader)
        val_loss, val_acc = trainer.validate(val_loader)

        logger.info(
            f"Epoch {epoch+1}/{epochs}: "
            f"Train Loss={train_loss:.4f}, "
            f"Val Loss={val_loss:.4f}, "
            f"Val Direction Acc={val_acc:.2%}"
        )

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            trainer.save_model(f"models/chitta_{model_type}_best.pt")

    logger.info(f"Training completed. Best validation loss: {best_val_loss:.4f}")

    return model
