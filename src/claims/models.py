
from enum import Enum

from pydantic import BaseModel


class QualifierKind(str, Enum):
    TIME = "TIME"
    LOCATION = "LOCATION"
    CONDITION = "CONDITION"

class ClaimQualifier(BaseModel):
    kind: QualifierKind
    value: str

class TargetAssociation(BaseModel):
    target_id: str

class ExtractedClaim(BaseModel):
    text: str
    qualifiers: list[ClaimQualifier] = []
    associations: list[TargetAssociation] = []

class ClaimExtractionOutcome(BaseModel):
    claims: list[ExtractedClaim] = []
