import uuid
from typing import Optional, Literal
from pydantic import BaseModel, model_validator
from app.core.errors import InvalidCorrectionError


class FeedbackRequest(BaseModel):
    event_id: uuid.UUID
    session_id: uuid.UUID
    feedback_type: Literal["correction", "confirmation"]
    corrected_class: Optional[str] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def validate_correction(self):
        if self.feedback_type == "correction" and not self.corrected_class:
            raise InvalidCorrectionError("We couldn't save that correction. Please select a valid material class.")
        return self


class FeedbackResponseData(BaseModel):
    correction_id: Optional[uuid.UUID] = None
    acknowledged: bool = True
