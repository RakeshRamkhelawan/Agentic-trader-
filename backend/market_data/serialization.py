
import msgpack
from typing import Any, Dict
from backend.market_data.models import UnifiedMarketEvent

def serialize_event(event: UnifiedMarketEvent) -> bytes:
    """
    Serialize UnifiedMarketEvent to MsgPack bytes.
    Uses generic dict conversion for speed/simplicity.
    """
    data = event.to_dict()
    # Remove None values to save bandwidth? 
    # For now, keep them for schema consistency or let msgpack handle Nil.
    # Msgpack 'None' maps to 'nil' which is efficient.
    return msgpack.packb(data, use_bin_type=True)

def deserialize_event(data: bytes) -> Dict[str, Any]:
    """
    Deserialize MsgPack bytes to Dict.
    Downstream consumers can instantiate UnifiedMarketEvent if needed.
    """
    return msgpack.unpackb(data, raw=False)
