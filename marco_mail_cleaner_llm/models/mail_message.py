from odoo import models, fields, api
import logging
import requests

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    cleaned_body = fields.Char("Email Pulita", default="")

    @api.model
    def create(self, vals):
        message = super(MailMessage, self).create(vals)
        if message.message_type == "email" and message.model == "crm.lead":
            self.with_delay(priority=1)._summarizeBody(message)        
        return message
    
    def _summarizeBody(self,message):
        try:
                res = requests.post(
                    "http://10.80.0.6:12345/summarize",
                    json={"content": message.body},
                    timeout=6000,
                )
                if res.status_code == 200:
                    cleaned_content=res.json()
                    _logger.error(cleaned_content)
                    if "status" in cleaned_content and cleaned_content["status"] == "ok":
                        message.write({"cleaned_body":cleaned_content["data"]["full_msg"]})
                    else:
                        _logger.warning(
                            "Impossibile ottenere l'email pulita per il messaggio ID %s",
                            message.id,
                        )
                return
        except:
            raise ValueError(f"Cannot reach the APIs")
        
    def action_custom_message(self):
        # La tua logica personalizzata per l'azione di messaggio
        # Ad esempio, invia una notifica, logga un messaggio o fai qualsiasi altra azione
        for message in self:
            # Esegui l'azione per ogni messaggio selezionato
            print(
                f"Eseguendo azione personalizzata per il messaggio con ID {message.id}"
            )
        return True

    def _get_message_format_fields(self):
        return [
            "id",
            "cleaned_body",
            "body",
            "date",
            "email_from",  # base message fields
            "message_type",
            "subtype_id",
            "subject",  # message specific
            "model",
            "res_id",
            "record_name",  # document related
            "starred_partner_ids",  # list of partner ids for whom the message is starred
        ]
