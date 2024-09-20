from pydantic import BaseModel, Field


class AnalyzeTextResponse(BaseModel):
    """Represents the response for object "create" endpoints."""

    print("**********ANALYZE TEXT RESPONSE************")

    success: bool = Field(..., examples=[True], description="Indicates if the text was successfully analyzed.")
    print(success)
    print("**********ANALYZE TEXT RESPONSE**********")
