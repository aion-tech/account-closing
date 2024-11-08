from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    industry_id = fields.Many2one('res.partner.industry', string='Industry',
        help='The industry of the partner. This field does not change the values of the partner related to the lead.')
    product_category_id = fields.Many2one('product.category', string='Product Category',
        help='The product category of the partner. This field does not change the values of the partner related to the lead.')
    partner_type_id = fields.Many2one('res.partner.type', string='Contact Type',
        help='The contact type of the partner. This field does not change the values of the partner related to the lead.')
    partner_applicability_id = fields.Many2one('res.partner.applicability', string='Partner Applicability',
        help='The partner applicability of the partner. This field does not change the values of the partner related to the lead.')

    def update_with_partner_data(self):
        for lead in self:
            if lead.partner_id:
                if lead.partner_id.industry_id:
                    lead.industry_id = lead.partner_id.industry_id.id
                if lead.partner_id.product_category_id:
                    lead.product_category_id = lead.partner_id.product_category_id.id
                if lead.partner_id.partner_type_id:
                    lead.partner_type_id = lead.partner_id.partner_type_id.id
                if lead.partner_id.partner_applicability_id:
                    lead.partner_applicability_id = lead.partner_id.partner_applicability_id.id

    # overriding the create so the logic also works
    # when the record is created outside the form view
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.partner_id:
            res.update_with_partner_data()
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.update_with_partner_data()

    # this method computes the data of the partner created from a new lead
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        res = super()._prepare_customer_values(partner_name, is_company, parent_id)
        res['industry_id'] = self.industry_id.id if self.industry_id else None
        res['product_category_id'] = self.product_category_id.id if self.product_category_id else None
        res['partner_type_id'] = self.partner_type_id.id if self.partner_type_id else None
        res['partner_applicability_id'] = self.partner_applicability_id.id if self.partner_applicability_id else None
        return res