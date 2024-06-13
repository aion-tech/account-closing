""" from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment

from ..dependencies.attendance import attendance_upserted
from ..dependencies.auth import api_key_auth_user
from ..schemas import Status

marco_api_router = APIRouter()


@marco_api_router.get("/attendance", response_model=Status)
def attendance(
    
    env: Annotated[Environment, Depends(odoo_env)],
    user: Annotated[
        Users,
        Depends(api_key_auth_user),
    ],
    attendance_id: Annotated[
        int,
        Depends(attendance_upserted),
    ],
) -> Status:
    
    return Status(id=attendance_id) """

from fastapi import APIRouter, Depends, HTTPException,Response
from typing import Annotated
from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment

from ..schemas import AckResponse, Attendance
from ..dependencies.attendance import attendance_upserted, decode_transaction
from ..dependencies.auth import api_key_auth_user

marco_api_router = APIRouter()

@marco_api_router.get("/attendance", response_model=AckResponse)
async def attendance(
    request: Annotated[Attendance, Depends()],
    env: Annotated[Environment, Depends(odoo_env)],
    user: Annotated[Users, Depends(api_key_auth_user)],
) -> AckResponse:
    """
    Create or update an attendance record, return the id
    """
    try:
        # Decodifica il messaggio
        decoded_message = decode_transaction(request)
        
        # Registrazione della transazione in Odoo
        attendance_id = attendance_upserted(env, decoded_message)
        
        return AckResponse(ack=1,message="Timbratura Registrata")
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la gestione della transazione: {str(e)}")
    
@marco_api_router.get("/batch")
async def batch(
    request: Annotated[Attendance, Depends()],
    env: Annotated[Environment, Depends(odoo_env)],
    user: Annotated[Users, Depends(api_key_auth_user)],
) :
    """
    Process a batch transaction and return acknowledgment.
    """
    try:
        # Decodifica il messaggio
        decoded_message = decode_transaction(request)
        
        # Registrazione della transazione in Odoo
        attendance_id = attendance_upserted(env, decoded_message)
        
        # Restituisce la risposta di acknowledgment
        return Response(content="ack=1", media_type="text/plain") #AckResponse(ack=1)
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la gestione della transazione batch: {str(e)}")

@marco_api_router.get("/keepalive")
async def keepalive() -> None:
    """
    Handle the keepalive request from the terminal and confirm server is online.
    """
    return None  # Respond with 200 OK by default
