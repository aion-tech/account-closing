from typing import Annotated, Any, Dict
from fastapi import Depends, HTTPException
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment
from odoo.exceptions import AccessError
from datetime import datetime,timedelta
import time

from ..schemas import Attendance  # Assicurati che `Attendance` sia importato correttamente dal tuo schema

from zoneinfo import ZoneInfo
import time
import logging


_logger = logging.getLogger(__name__)



def decode_transaction(request: Attendance) -> dict:
    try:
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

        # Creazione oggetto datetime con fuso orario specifico (es. Europe/Rome)
        local_tz = ZoneInfo('Europe/Rome')
        datetime_dt = datetime(year, month, day, hour, minute, tzinfo=local_tz)
        datetime_utc = datetime_dt.astimezone(ZoneInfo('UTC'))

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
            'datetime': datetime_utc,
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
    Upsert an attendance, return its id or raise HTTPException if errors occur.
    """
    employee = env["hr.employee"].search([("barcode", "=", payload['user_id'])], limit=1)
    if not employee:
        return {"firstLine":"ERRORE","secondLine":"Dipendente non esiste","beeps":5}
        #raise HTTPException(status_code=404, detail="Dipendente non trovato")

    dt = payload['datetime'].replace(tzinfo=None)  # Usa datetime naive

    try:
        department = employee.department_id
        if not department:
            return {"firstLine":"ERRORE","secondLine":"Dipartimento non assegnato","beeps":4}
            #raise HTTPException(status_code=400, detail="Nessun dipartimento assegnato al dipendente")
        
        department_name = department.name
    except AccessError:
        return {"firstLine":"ERRORE","secondLine":"Non autorizzato","beeps":5}
        #raise HTTPException(status_code=403, detail="Accesso non autorizzato ai record del dipartimento")

    if department_name == 'Produzione':
        return handle_worker_attendance(env, employee, dt, payload['direction'])
        
    else:
        return handle_employee_attendance(env, employee, dt)
          # Timbratura per impiegati, già gestita, nessun ID da restituire


def handle_worker_attendance(env, employee, dt, direction):
    """Gestisce le timbrature per gli operai."""
    if direction == "check_out":
        # Cerca una transazione di check-in aperta per il dipendente
        attendance = env["hr.attendance"].search(
            [("check_out", "=", False), ("employee_id", "=", employee.id),("check_in", "<=", dt)], limit=1
        )
        if attendance:
            # Chiudi la transazione aperta con check-out
            attendance.write({"check_out": dt})
            return {"firstLine":"ARRIVEDORCI","secondLine":"Ciao Bela/o","beeps":100}
        else:
            return {"firstLine":"ERRORE","secondLine":"Ingresso non timbrato","beeps":7}
    else:
        # Cerca se c'è già una timbratura di check-in coperta dall'intervallo
        overlapping_attendance = env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                ("check_in", "<=", dt),
                ("check_out", ">=", dt)
            ], limit=1
        )
        if overlapping_attendance:
            # Se esiste già una timbratura che copre questo intervallo, ignora
            return {"firstLine":"ERRORE","secondLine":"Timbratura gia' esitente","beeps":4}

        # Cerca una transazione di check-in aperta e chiudila se esiste
        open_check_in = env["hr.attendance"].search(
            [("check_out", "=", False), ("employee_id", "=", employee.id)], limit=1
        )
        if open_check_in:
           return  {"firstLine":"ERRORE","secondLine":"Timbra prima l'uscita","beeps":4}

        # Crea una nuova transazione di check-in
        env["hr.attendance"].create(
            {
                "check_in": dt,
                "employee_id": employee.id,
            }
        )
        return {"firstLine":"BENVENUTO","secondLine":f"{employee.name}","beeps":1}

def handle_employee_attendance(env, employee, dt):
    """Gestisce le timbrature per gli impiegati, creando tutte le timbrature necessarie per coprire la giornata."""
    start_of_day = datetime.combine(dt.date(), datetime.min.time()).replace(tzinfo=None)
    end_of_day = start_of_day + timedelta(days=1)
    
    existing_attendance = env["hr.attendance"].search([
        ("employee_id", "=", employee.id),
        ("check_in", ">=", start_of_day),
        ("check_in", "<", end_of_day)
    ], limit=1)
    
    if existing_attendance:
        return {"firstLine":"ERRORE","secondLine":"Hai gia' timbrato","beeps":99}

    
    return create_employee_attendances(env, employee, dt)

def create_employee_attendances(env, employee, dt):
    """Crea tutte le timbrature necessarie per coprire la giornata secondo la working schedule."""
    working_schedule = employee.resource_calendar_id
    if not working_schedule:
        # Eccezione: Nessun calendario di lavoro assegnato
        return {"firstLine":"ERRORE","secondLine":"Non hai un calendario","beeps":8}
    
    local_tz = ZoneInfo('Europe/Rome')  # Supponendo che Europe/Rome sia il fuso orario locale
    check_ins = []
    
    # Crea le timbrature in base alla giornata lavorativa
    for attendance in working_schedule.attendance_ids:
        if int(attendance.dayofweek) == dt.weekday():
            # Calcola gli orari di check-in e check-out in ora locale
            check_in_local = datetime.combine(dt.date(), (datetime.min + timedelta(hours=attendance.hour_from)).time()).replace(tzinfo=local_tz)
            check_out_local = datetime.combine(dt.date(), (datetime.min + timedelta(hours=attendance.hour_to)).time()).replace(tzinfo=local_tz)
            
            # Converti in UTC
            check_in_time = check_in_local.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
            check_out_time = check_out_local.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
            
            check_ins.append({
                "check_in": check_in_time,
                "check_out": check_out_time,
                "employee_id": employee.id,
            })
    
    if check_ins:
        env["hr.attendance"].create(check_ins)
    return {"firstLine":"BENVENUTO","secondLine":f"{employee.name}","beeps":100}