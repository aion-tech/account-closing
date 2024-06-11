from typing import Annotated, Any, Dict
from fastapi import Depends, HTTPException
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment
from datetime import datetime
import time

from ..schemas import Attendance  # Assicurati che `Attendance` sia importato correttamente dal tuo schema

def decode_transaction(request: Attendance) -> dict:
    try:
        # Decodifica dell'ID Utente
        user_id = request.trsn[3:7]
        
        # Formattazione data e ora
        year = int(request.date[:4])
        month = int(request.date[4:6])
        day = int(request.date[6:8])
        hour = int(request.time[:2])
        minute = int(request.time[2:4])
        second = int(request.time[4:6])
        
        # Creazione oggetto datetime
        timestamp_dt = datetime(year, month, day, hour, minute, second)
        timestamp = int(time.mktime(timestamp_dt.timetuple()))
        
        # Determinazione del tipo di transazione
        if request.trsn.endswith("00"):
            direction = 'check_in'
        elif request.trsn.endswith("01"):
            direction = 'check_out'
        else:
            raise ValueError("Tipo di transazione sconosciuto")

        # Output decodificato come dizionario
        return {
            'user_id': user_id,
            'terminal_id': request.terminal_id,
            'macaddr': request.macaddr,
            'timestamp': timestamp,
            'direction': direction
        }
    except Exception as e:
        raise ValueError(f"Errore durante la decodifica: {e}")

def attendance_upserted(
    env: Annotated[Environment, Depends(odoo_env)],
    payload: Annotated[Dict[str, Any], Depends()],
) -> int:
    """
    Upsert an attendance, return its id or raise HTTPException if errors occur
    """
    
    # Cerca il dipendente tramite l'ID Utente decodificato (barcode)
    employee = env["hr.employee"].search([("barcode", "=", payload['user_id'])], limit=1)
    if not employee:
        # Se non viene trovato alcun dipendente, solleva un'eccezione
        raise HTTPException(status_code=404, detail=f"Nessun dipendente trovato per l'ID Utente {payload['user_id']}")

    dt = datetime.fromtimestamp(payload['timestamp'])
    if payload['direction'] == "check_out":
        # Cerca una transazione di presenza aperta
        attendance = env["hr.attendance"].search(
            [("check_out", "=", False), ("employee_id", "=", employee.id)], limit=1
        )
        if attendance:
            # Aggiorna la transazione aperta con check_out
            attendance.write(
                {
                    "check_out": dt,
                }
            )
            return attendance.id
        else:
            # Solleva un'eccezione se non esiste una transazione check_in aperta
            raise HTTPException(status_code=400, detail="Nessuna transazione check_in aperta trovata per questo dipendente")
    else:
        # Crea una nuova transazione check_in
        attendance = env["hr.attendance"].create(
            {
                "check_in": dt,
                "employee_id": employee.id,
            }
        )
        return attendance.id
