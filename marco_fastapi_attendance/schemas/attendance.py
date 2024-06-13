from pydantic import BaseModel,Field
from typing import Optional


class Attendance(BaseModel):
    trsn: str = Field(..., description="Transaction message")  # Obbligatorio
    """  badge: Optional[str] = Field(None, description="Employee badge ID")  # Opzionale
    terminal_id: Optional[str] = Field(None, alias="id", description="Terminal ID")  # Opzionale
    macaddr: Optional[str] = Field(None, alias="ip", description="MAC Address")  # Opzionale
    date: Optional[str] = Field(None, description="Date in format YYYYMMDD")  # Opzionale
    time: Optional[str] = Field(None, description="Time in format HHMMSS")  # Opzionale
    """