"""
Transformer Model voor Chitta Forecasting

Voordelen over LSTM:
- Betere long-range dependencies (attention mechanism)
- Parallel processing van sequences
- Geen vanishing gradient probleem
- State-of-the-art voor time series forecasting
"""

import logging
import math

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """Positional encoding voor Transformer."""

    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Pre-compute positional encodings
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]

        self.register_buffer("pe", pe)

    def forward(self, x):
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class ChittaTransformer(nn.Module):
    """
    Transformer model voor time series forecasting.

    Architecture:
    - Input projection: features -> d_model
    - Positional encoding
    - N Transformer encoder layers
    - Global average pooling
    - FC layers -> output
    """

    def __init__(
        self,
        input_size: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        output_size: int = 1,
    ):
        super(ChittaTransformer, self).__init__()

        self.d_model = d_model

        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(d_model, dim_feedforward // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward // 2, output_size),
        )

        self._init_weights()

        logger.info(
            f"ChittaTransformer initialized: d_model={d_model}, layers={num_layers}, heads={nhead}"
        )

    def _init_weights(self):
        """Initialize weights."""
        initrange = 0.1
        self.input_projection.weight.data.uniform_(-initrange, initrange)
        for layer in self.fc:
            if isinstance(layer, nn.Linear):
                layer.weight.data.uniform_(-initrange, initrange)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: [batch_size, seq_len, input_size]

        Returns:
            [batch_size, output_size]
        """
        # Project input
        x = self.input_projection(x)  # [batch, seq, d_model]

        # Add positional encoding
        x = self.pos_encoder(x)

        # Transformer encoding
        encoded = self.transformer_encoder(x)  # [batch, seq, d_model]

        # Global average pooling
        pooled = encoded.mean(dim=1)  # [batch, d_model]

        # Output
        output = self.fc(pooled)

        return output


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer - Advanced architecture voor time series.

    Combines:
    - Static covariates (elemental features)
    - Temporal features (price history)
    - Attention mechanism
    """

    def __init__(
        self,
        input_size: int,
        static_size: int = 5,  # fire, water, air, earth, ether
        hidden_size: int = 160,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
        output_size: int = 1,
    ):
        super().__init__()

        # Variable selection networks
        self.static_vsn = VariableSelectionNetwork(static_size, hidden_size, dropout)
        self.temporal_vsn = VariableSelectionNetwork(input_size, hidden_size, dropout)

        # LSTM encoder
        self.lstm_encoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )

        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )

        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, x_temporal: torch.Tensor, x_static: torch.Tensor = None):
        """
        Args:
            x_temporal: [batch, seq, input_size] - time series features
            x_static: [batch, static_size] - static features (elemental)
        """
        # Variable selection
        temporal_features = self.temporal_vsn(x_temporal)

        if x_static is not None:
            static_features = self.static_vsn(x_static)
            # Combine
            temporal_features = temporal_features + static_features.unsqueeze(1)

        # LSTM encoding
        lstm_out, _ = self.lstm_encoder(temporal_features)

        # Attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Combine LSTM en attention
        combined = torch.cat([lstm_out[:, -1, :], attn_out[:, -1, :]], dim=-1)

        # Output
        return self.fc(combined)


class VariableSelectionNetwork(nn.Module):
    """Variable Selection Network voor TFT."""

    def __init__(self, input_size: int, hidden_size: int, dropout: float):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        # Individual linear layers voor elke input
        self.single_variable_grns = nn.ModuleList(
            [GatedResidualNetwork(input_size, hidden_size, dropout) for _ in range(input_size)]
        )

        # Variable selection weights
        self.selection_weights = GatedResidualNetwork(input_size * hidden_size, input_size, dropout)

    def forward(self, x):
        """x: [batch, seq, input_size] of [batch, input_size]"""
        if len(x.shape) == 2:
            x = x.unsqueeze(1)  # [batch, 1, input_size]

        # Apply GRN aan elke variable apart
        var_outputs = []
        for i, grn in enumerate(self.single_variable_grns):
            var_input = x[:, :, i : i + 1]
            var_output = grn(var_input)
            var_outputs.append(var_output)

        # Stack
        stacked = torch.stack(var_outputs, dim=-1)  # [batch, seq, hidden, input_size]

        # Selection weights
        flattened = stacked.view(x.size(0), x.size(1), -1)
        weights = torch.softmax(self.selection_weights(flattened), dim=-1)

        # Weighted combination
        weighted = stacked * weights.unsqueeze(2)
        output = weighted.sum(dim=-1)

        return output


class GatedResidualNetwork(nn.Module):
    """GRN - Gated Residual Network."""

    def __init__(self, input_size: int, output_size: int, dropout: float):
        super().__init__()
        self.fc1 = nn.Linear(input_size, output_size)
        self.elu = nn.ELU()
        self.fc2 = nn.Linear(output_size, output_size)
        self.dropout = nn.Dropout(dropout)
        self.gate = nn.Linear(output_size, output_size)
        self.layer_norm = nn.LayerNorm(output_size)

        if input_size != output_size:
            self.skip = nn.Linear(input_size, output_size)
        else:
            self.skip = None

    def forward(self, x):
        residual = x if self.skip is None else self.skip(x)

        hidden = self.fc1(x)
        hidden = self.elu(hidden)
        hidden = self.fc2(hidden)
        hidden = self.dropout(hidden)

        gate = torch.sigmoid(self.gate(hidden))
        hidden = hidden * gate

        return self.layer_norm(hidden + residual)
