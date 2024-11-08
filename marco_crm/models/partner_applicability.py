from odoo import models, fields

class PartnerApplicability(models.Model):
    _name = 'res.partner.applicability'
    _description = 'Partner Applicability'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')