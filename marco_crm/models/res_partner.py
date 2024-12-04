from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type_id = fields.Many2one('res.partner.type', string='Contact Type')
    partner_applicability_id = fields.Many2one('res.partner.applicability', string='Partner Applicability')
    product_category_id = fields.Many2one('product.category', string='Product Category')