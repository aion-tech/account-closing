from odoo.tests.common import TransactionCase

class TestCommon(TransactionCase):

    def setUp(self):
        super(TestCommon, self).setUp()
        self.CrmLead = self.env['crm.lead']
        self.industry1 = self.env['res.partner.industry'].create({
            'name': 'Test Industry 1'
            })
        self.industry2 = self.env['res.partner.industry'].create({
            'name': 'Test Industry 2'
            })
        self.product_category1 = self.env['product.category'].create({
            'name': 'Test Category 1'
            })
        self.product_category2 = self.env['product.category'].create({
            'name': 'Test Category 2'
            })

        self.partner_type1 = self.env['res.partner.type'].create({
            'name': 'Test Partner Type 1'
            })
        self.partner_type2 = self.env['res.partner.type'].create({
            'name': 'Test Partner Type 2'
            })
        self.partner_applicability1 = self.env['res.partner.applicability'].create({
            'name': 'Test Partner Applicability 1'
            })
        self.partner_applicability2 = self.env['res.partner.applicability'].create({
            'name': 'Test Partner Applicability 2'
            })
        
        self.contact1 = self.env['res.partner'].create({
            'name': 'Test Contact 1',
            'partner_type_id': self.partner_type1.id,
            'partner_applicability_id': self.partner_applicability1.id,
            'product_category_id': self.product_category1.id,
            'industry_id': self.industry1.id,
            })