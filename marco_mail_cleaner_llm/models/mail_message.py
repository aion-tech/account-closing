from odoo import models, fields, api
import logging
import requests

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    cleaned_body = fields.Html("Email Pulita", default="", sanitize_style=True)

    @api.model
    def create(self, vals):
        message = super(MailMessage, self).create(vals)
        _logger.error(message)
        if message.message_type == "email" and message.model == "crm.lead":
            
            """ cleaned_content = self.with_delay(priority=5).requests.post(
                "http://10.80.0.5:12345/summarize",
                json={
                    "content":message.body
                },

            ) """
            cleaned_content="Hellooo"
            if cleaned_content:
                message.cleaned_body = cleaned_content
            else:
                _logger.warning(
                    "Impossibile ottenere l'email pulita per il messaggio ID %s",
                    message.id,
                )
        return message

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
