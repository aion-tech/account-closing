from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel


class Status(BaseModel):
    """Response status & id of the created/updated odoo record"""

    status: str = "ok"
    id: Optional[int] = None
