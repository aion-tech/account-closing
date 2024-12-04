from odoo import models, fields

class PartnerType(models.Model):
    _name = 'res.partner.type'
    _description = 'Partner Type'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')