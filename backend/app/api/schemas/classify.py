import base64
import uuid
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.errors import InvalidInputError, ImageTooLargeError, UnsupportedFormatError


class ConsentSchema(BaseModel):
    image_upload: bool = False
    analytics: bool = True
    location: bool = False


class ClassifyRequest(BaseModel):
    session_id: uuid.UUID
    input_type: Literal["image", "text"] = "text"
    image_b64: Optional[str] = None
    description: Optional[str] = None
    ward_id: Optional[str] = None
    consent: ConsentSchema = Field(default_factory=ConsentSchema)

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.image_b64 and not self.description:
            raise InvalidInputError("Please add a photo or describe the item before submitting.")
        
        if self.image_b64:
            try:
                # Remove data header if present (e.g. data:image/jpeg;base64,)
                raw_b64 = self.image_b64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                
                decoded = base64.b64decode(raw_b64)
                if len(decoded) > 5 * 1024 * 1024:  # 5 MB
                    raise ImageTooLargeError("That photo is too large. Please try a smaller photo.")
            except ImageTooLargeError:
                raise
            except Exception:
                raise UnsupportedFormatError("We couldn't read that file. Please use a JPEG or PNG photo.")

        return self


class Top3Item(BaseModel):
    model_config = {"populate_by_name": True}
    class_: str = Field(..., alias="class")
    confidence: float


class MaterialDetail(BaseModel):
    name: str
    category: str
    disposal_bin: str
    recovery_potential: str
    next_life: str
    recovery_channel: str
    contamination_notes: str


class GuidanceDetail(BaseModel):
    bin_label: str
    action: str
    do: List[str]
    do_not: List[str]


class ClassifyResponseData(BaseModel):
    event_id: uuid.UUID
    predicted_class: str
    confidence: float
    confidence_label: str
    top3: List[Top3Item]
    material: MaterialDetail
    guidance: GuidanceDetail
