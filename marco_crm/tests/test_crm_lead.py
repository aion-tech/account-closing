from odoo.tests.common import TransactionCase, Form
from .common import TestCommon


class TestCrmLead(TestCommon):

    def test_crm_lead_create_and_update_with_partner_data(self):
        lead = self.CrmLead.create({
            'name': 'Test Lead',
            'partner_id': self.contact1.id,
            })
        self.assertEqual(lead.partner_type_id, self.partner_type1, 'Partner Type not set')
        self.assertEqual(lead.partner_applicability_id, self.partner_applicability1, 'Partner Applicability not set')
        self.assertEqual(lead.product_category_id, self.product_category1, 'Product Category not set')
        self.assertEqual(lead.industry_id, self.industry1, 'industry1 not set')

    """
    Use Case prepopolamento lead:
    1. Utente crea nuova opportunità
    2. Utente popola il campo cliente
    3. Sistema recupera le informazioni dall'anagrafica e popola i campi:
    - Settore
    - Tipologia
    - Applicazione
    - Categoria prodotto
    """

    def test_crm_lead_onchange_partner_id(self):
        with Form(self.CrmLead) as lead:
            lead.name = 'Test Lead'
            lead.partner_type_id = self.partner_type2
            lead.partner_applicability_id = self.partner_applicability2
            lead.product_category_id = self.product_category2
            lead.industry_id = self.industry2
        bonus = lead.save()
        self.assertEqual(bonus.partner_type_id, self.partner_type2, 'Partner Type not set')
        self.assertEqual(bonus.partner_applicability_id, self.partner_applicability2, 'Partner Applicability not set')
        self.assertEqual(bonus.product_category_id, self.product_category2, 'Product Category not set')
        self.assertEqual(bonus.industry_id, self.industry2, 'industry1 not set')
        
        #edit previous lead record with Form
        with Form(bonus) as lead:
            lead.partner_id = self.contact1
        lead.save()

        self.assertEqual(bonus.partner_type_id, self.partner_type1, 'Partner Type not set')
        self.assertEqual(bonus.partner_applicability_id, self.partner_applicability1, 'Partner Applicability not set')
        self.assertEqual(bonus.product_category_id, self.product_category1, 'Product Category not set')
        self.assertEqual(bonus.industry_id, self.industry1, 'industry1 not set')

    """
    Use Case popolamento contatto:
    1. Utente crea nuova opportunità
    2. Utente popola opportunità
    3. Utente clicca su crea contatto (o su nuovo preventivo e poi su crea contatto)
    4. Sistema crea nuovo contatto e riporta sull'anagrafica, tra le altre informazioni già previste, anche i valori dei campi:
    - Settore
    - Tipologia
    - Applicazione
    - Categoria prodotto
    """

    def test_crm_lead_create_partner(self):
        lead = self.CrmLead.create({
            'name': 'Test Lead 2',
            'partner_name': 'Test Contact 2',
            'partner_type_id': self.partner_type2.id,
            'partner_applicability_id': self.partner_applicability2.id,
            'product_category_id': self.product_category2.id,
            'industry_id': self.industry2.id,
            })
        contact = self.env['res.partner'].search([('name', '=', 'Test Contact 2')])
        self.assertFalse(contact, 'Contact created when it should not have been')

        wizard = Form(self.env['crm.lead2opportunity.partner'].with_context({
            'active_model': 'crm.lead',
            'active_id': lead.id,
            'active_ids': lead.ids,
        }))
        wizard.name = 'convert'
        wizard.action = 'create'
        wiz = wizard.save()
        wiz.action_apply()
        contact = self.env['res.partner'].search([('name', '=', 'Test Contact 2')])
        self.assertTrue(contact, 'Contact not created')
        self.assertEqual(contact.partner_type_id, self.partner_type2, 'Partner Type not set')
        self.assertEqual(contact.partner_applicability_id, self.partner_applicability2, 'Partner Applicability not set')
        self.assertEqual(contact.product_category_id, self.product_category2, 'Product Category not set')
        self.assertEqual(contact.industry_id, self.industry2, 'industry1 not set')