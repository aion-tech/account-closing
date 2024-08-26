# marco_stock_location/models/stock_location.py

from odoo import models, api, fields
import requests
from urllib.parse import quote
from odoo.exceptions import UserError
import logging
import json


_logger = logging.getLogger(__name__)


class Location(models.Model):
    _inherit = 'stock.location'

    m_label_type = fields.Selection([
        ('vertical', 'Verticale'),
        ('horizontal', 'Orizzontale'),
        ('large', 'Grande')
    ], string='Tipo di Etichetta', default='horizontal')

    m_storage_type = fields.Selection([
        ('corsia', 'Corsia'),
        ('perimetrale', 'Perimetrale'),
        ('isola', 'Isola'),
        ('zona_a_terra', 'Zona a Terra')
    ], string='Tipo di Stoccaggio', default='corsia')

    @api.depends('name', 'location_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.location_id:
                location.complete_name = '%s/%s' % (location.location_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    def print_label(self,url_with_params,complete_name):
        try:
                # Invia la richiesta GET
                response = requests.get(url_with_params, timeout=15)
                if response.status_code == 200:
                    response_content = json.loads(response.content.decode('utf-8-sig'))
                    messages = response_content.get('Messages', [])
                    printer_name = ""
                    # Accede direttamente al secondo messaggio
                    for message in messages:
                        text = message.get('Text', '')
                        printer_index = text.find("Printer: ")
                        if printer_index != -1:
                            # Estrai il nome della stampante
                            printer_name = text[printer_index + len("Printer: "):].strip().replace('\\\\', '\\').split('\\')[-1]
                            break  # Esci dal loop una volta trovato il nome della stampante

                    # Notifica l'utente che l'etichetta è stata stampata con successo
                    self.env.user.notify_success(
                        message=f"L'etichetta per {complete_name} è stata stampata con successo sulla stampante {printer_name}.",   
                    )
                else:
                    # Notifica l'utente che ci sono stati problemi durante la stampa dell'etichetta
                    self.env.user.notify_danger(
                        message=f"Problemi nella stampa dell'etichetta per {complete_name}. Verificare i dettagli nei log.",
                    )
        except requests.exceptions.Timeout:
            self.env.user.notify_danger(
                message=f"La figa di stampante non rispode",
            )
        except requests.RequestException as e:
            # Notifica l'utente dell'errore durante la richiesta API
            self.env.user.notify_danger(
                message=f"Errore durante l'invio della richiesta per la location {complete_name}: {e}",
            )
        

    def print_locations_label_via_api(self):
        base_url = f"http://labels.marco.it/Integration/locationWMS"
        
        # Ordina i record per corridoio, scaffale (rack) e nome
        sorted_records = sorted(self, key=lambda record: (record.corridor,record.row, record.rack,  record.name))
        if len(sorted_records) >1:
            self.env.user.notify_info(
                            message=f"Stampa di {len(sorted_records)} etichette avviata, collegamento alla stampante in corso...",   
                    )
        else:
            self.env.user.notify_info(
                            message=f"Stampa dell'etichetta avviata, collegamento alla stampante in corso...",   
                    )
        for record in sorted_records:
            if not (record.m_label_type or record.m_storage_type):
                    self.env.user.notify_danger(
                        message=f"Problemi nella stampa dell'etichetta per {record.complete_name}. Verificare i dettagli nei log.",
                    )
                    continue
            match record.m_storage_type:
                case 'corsia':    
                    titlelabel = "PIANO"
                    titlevalue = record.level
                    subtitle = record.barcode[2:]  # Rimuove il prefisso '92' dal barcode
                    par1label = "CORSIA"
                    par1value = record.corridor
                    par2label = "CAMPATA"
                    par2value = record.rack
                    par3label = "POSIZIONE"
                    par3value = record.name
                case 'perimetrale':
                    titlelabel = "PIANO"
                    titlevalue = record.level
                    subtitle = record.barcode[2:]  # Rimuove il prefisso '92' dal barcode
                    par1label = "SCAFFALE"
                    par1value = record.corridor
                    par2label = "COLONNA"
                    par2value = record.rack
                    par3label = "POSIZIONE"
                    par3value = record.name
                case 'isola':
                    titlelabel = "PIANO"
                    titlevalue = record.level
                    subtitle = record.barcode[2:]  # Rimuove il prefisso '92' dal barcode
                    par1label = "ISOLA"
                    par1value = record.corridor
                    par2label = "COLONNA"
                    par2value = record.rack
                    par3label = "POSIZIONE"
                    par3value = record.name
                case 'zona_a_terra':
                    titlelabel = "ZONA A TERRA"
                    titlevalue = record.corridor
                    subtitle = record.barcode[2:]  # Rimuove il prefisso '92' dal barcode
                    par1label = "RIGA"
                    par1value = record.level
                    par2label = "COLONNA"
                    par2value = record.rack
                    par3label = "POSIZIONE"
                    par3value = record.name

            # Costruisci manualmente i parametri della query
            params = {
                'barcode': record.barcode,
                'titlelabel': titlelabel,
                'titlevalue': titlevalue,
                'subtitle': subtitle,
                'par1label': par1label,
                'par1value': par1value,
                'par2label': par2label,
                'par2value': par2value,
                'par3label': par3label,
                'par3value': par3value,
            }

            # Codifica i parametri manualmente
            query_string = '&'.join(f"{key}={quote(str(value))}" for key, value in params.items())

            # Costruisce l'URL completo con i parametri
            url_with_params = f"{base_url}/{record.m_label_type}/Execute?{query_string}"
            self.with_delay(priority=1).print_label(url_with_params,record.complete_name)
           
    