from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    marco_llm_api_url = fields.Char(
        string="MARCO LLaMadoo API URL",
        config_parameter='marco_mail_cleaner_llm.marco_llm_api_url',
        default="https://summarize.marco.it",
        help="URL base delle API per il modulo MARCO LLaMadoo",
    )
       
    marco_llm_api_endpoint = fields.Char(
        string="MARCO LLaMadoo API Endpoint",
        config_parameter='marco_mail_cleaner_llm.marco_llm_api_endpoint',
        default="/summarize",
        help="Endpoint API per il modulo MARCO LLaMadoo",
    )
    marco_llm_api_response_field = fields.Char(
        string="MARCO LLaMadoo API Response Field",
        config_parameter='marco_mail_cleaner_llm.marco_llm_api_response_field',
        default="data.short_summary",
        help="Campo della risposta delle API contenente il messaggio elaborato",
    )
