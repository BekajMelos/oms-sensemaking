"""NLP Sensemaker models"""

from pydantic import BaseModel


class TextSubmission(BaseModel):
    text: str
