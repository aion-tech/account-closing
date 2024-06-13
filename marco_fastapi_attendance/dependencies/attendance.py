from typing import Annotated, Any, Dict
from fastapi import Depends, HTTPException
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment
from datetime import datetime
import time

from ..schemas import Attendance  # Assicurati che `Attendance` sia importato correttamente dal tuo schema

from datetime import datetime
import time
import re

def decode_transaction(request: Attendance) -> dict:
    try:
        """  # Verifica del formato del messaggio di transazione
        if not re.match(r'^A27\d{5}\d{2}\d{2}\d{2}\d{2}\d{2}\d{2}00$', request.trsn):
            raise ValueError("Formato del messaggio di transazione non valido") """

        # Decodifica dell'ID Utente
        user_id = int(request.trsn[3:8])  # 5 caratteri per l'ID utente

        # Tipo di transazione
        transaction_type = request.trsn[8:10]  # 2 caratteri per il tipo di transazione

        # Estrazione di data e ora dalla transazione
        year = int('20' + request.trsn[10:12])  # '20' + YY
        month = int(request.trsn[12:14])  # MM
        day = int(request.trsn[14:16])  # DD
        hour = int(request.trsn[16:18])  # hh
        minute = int(request.trsn[18:20])  # mm
        

        # Validazione dei valori di data e ora
        if not (1 <= month <= 12):
            raise ValueError(f"Valore del mese non valido: {month}")
        if not (1 <= day <= 31):
            raise ValueError(f"Valore del giorno non valido: {day}")
        if not (0 <= hour <= 23):
            raise ValueError(f"Valore dell'ora non valido: {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Valore dei minuti non valido: {minute}")

        # Creazione oggetto datetime
        timestamp_dt = datetime(year, month, day, hour, minute)
        timestamp = int(time.mktime(timestamp_dt.timetuple()))

        # Determinazione del tipo di transazione
        if transaction_type == "00":
            direction = 'check_in'
        elif transaction_type == "01":
            direction = 'check_out'
        else:
            raise ValueError("Tipo di transazione sconosciuto")

        # Output decodificato come dizionario
        return {
            'user_id': user_id,
            'timestamp': timestamp,
            'direction': direction,
            
        }
    except ValueError as ve:
        raise ValueError(f"Errore durante la decodifica: {ve}")
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
            attendance = env["hr.attendance"].create(
            {
                "check_in": dt,
                "check_out": dt,
                "employee_id": employee.id,
            }
            )
            return attendance.id
            #raise HTTPException(status_code=400, detail="Nessuna transazione check_in aperta trovata per questo dipendente")
    else:
        # Crea una nuova transazione check_in
        attendance = env["hr.attendance"].create(
            {
                "check_in": dt,
                "employee_id": employee.id,
            }
        )
        return attendance.id
