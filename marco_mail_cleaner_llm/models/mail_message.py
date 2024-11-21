from odoo import models, fields, api
import logging
import requests

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    cleaned_body = fields.Char("Email Pulita", default="")

    @api.model_create_multi
    def create(self, vals):
        messages = super(MailMessage, self).create(vals)
        for message in messages:
            if message.message_type == "email" and message.model == "crm.lead":
                self.with_delay(priority=1,max_retries=3)._summarizeBody(message)        
            return message

    def _summarizeBody(self, message):
        try:
            api_url = self.env['ir.config_parameter'].sudo().get_param('marco_mail_cleaner_llm.marco_llm_api_url')
            api_endpoint = self.env['ir.config_parameter'].sudo().get_param('marco_mail_cleaner_llm.marco_llm_api_endpoint')
            api_response_field = self.env['ir.config_parameter'].sudo().get_param('marco_mail_cleaner_llm.marco_llm_api_response_field')

            # Controllo dei parametri e lancio di errori personalizzati
            missing_params = []
            if not api_url:
                missing_params.append("MARCO LLaMadoo API URL")
            if not api_endpoint:
                missing_params.append("MARCO LLaMadoo API Endpoint")
            if not api_response_field:
                missing_params.append("MARCO LLaMadoo API Response Field")

            if missing_params:
                raise ValueError(f"I seguenti parametri non sono configurati nelle impostazioni generali: {', '.join(missing_params)}")

            # Componi l'URL completo
            full_url = f"{api_url}{api_endpoint}"

            # Chiamata all'API
            res = requests.post(
                full_url,
                json={"content": message.body},
                timeout=6000,
            )
            
            if res.status_code == 200:
                cleaned_content = res.json()
                _logger.error(cleaned_content)

                # Estrarre il campo configurabile dalla risposta
                response_keys = api_response_field.split('.')  # Divide i livelli (es. "data.full_msg")
                response_value = cleaned_content
                for key in response_keys:
                    response_value = response_value.get(key, None)
                    if response_value is None:
                        _logger.warning(
                            "Il campo %s non è presente nella risposta dell'API per il messaggio ID %s",
                            api_response_field, message.id
                        )
                        return

                # Aggiorna il messaggio con il valore pulito
                message.write({"cleaned_body": response_value})
            else:
                _logger.warning(
                    "Errore API per il messaggio ID %s: %s",
                    message.id, res.status_code
                )
            return
        except Exception as e:
            _logger.error("Errore durante la connessione alle API: %s", e)
            raise ValueError("Cannot reach the APIs")

        
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
