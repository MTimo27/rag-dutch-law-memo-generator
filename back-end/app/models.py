from pydantic import BaseModel

class MemoRequest(BaseModel):
    disputedDecision: str
    desiredOutcome: str
    criticalFacts: str
    applicableLaw: str
    recipients: str
