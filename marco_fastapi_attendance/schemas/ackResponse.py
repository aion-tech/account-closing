from pydantic import BaseModel, Field
from typing import Optional


class AckResponse(BaseModel):
    ack: int = Field(..., description="Acknowledgment")
    message: Optional[str] = Field(None, description="Message to display on terminal")

#class Status(BaseModel):
    """Response status & id of the created/updated odoo record"""

   # status: str = "ok"
    #id: Optional[int] = None
