from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FiscalDocumentType(models.Model):
    _inherit = 'fiscal.document.type'

    created_from_ddt = fields.Boolean(string="Created from DDT")

    @api.constrains('created_from_ddt')
    def _check_unique_created_from_ddt(self):
        for record in self:
            if record.created_from_ddt:
                existing_record = self.search([
                    ('created_from_ddt', '=', True),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing_record:
                    raise ValidationError("Only one record can have 'Created from DDT' set to True.")