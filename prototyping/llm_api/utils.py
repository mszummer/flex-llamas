
import json
from enum import Enum
from pydantic import BaseModel

def serialize(request: BaseModel) -> str:
    """
    Turns a pydantic model (request param) into serialized JSON string format.
    Uses the EnumEncoder class to get the value of the Enum so we can model dump without error.
    """
    class EnumEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Enum):
                return obj.value
            return super().default(obj)
    return json.dumps(request.model_dump(), cls=EnumEncoder)
