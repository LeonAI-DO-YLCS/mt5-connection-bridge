from pydantic import BaseModel

class CompatibilityProfile(BaseModel):
    name: str
    retry_aggressiveness: str
    optional_field_handling: str
    gating_strictness: str
    warning_verbosity: str
