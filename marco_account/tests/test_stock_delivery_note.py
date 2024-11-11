from odoo.exceptions import ValidationError
from odoo.tests.common import tagged, TransactionCase

@tagged('post_install', '-at_install', 'marco')
class TestStockDeliveryNote(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockDeliveryNote, cls).setUpClass()
        cls.ddt = cls.env["stock.delivery.note"].create({
            "name": "Test DDT",
            "partner_id": cls.env.ref("base.res_partner_2").id,
            "delivery_date": "2021-01-01",
            "delivery_note_line_ids": [
                (0, 0, {
                    "product_id": cls.env.ref("product.product_product_4").id,
                    "quantity": 1,
                }),
            ],
        })
        cls.ddt.action_confirm()

    def test_action_invoice(self):
        self.ddt.action_invoice()
        self.assertTrue(self.ddt.invoice_ids)
        self.assertTrue(self.ddt.invoice_ids.fiscal_document_type_id)
        self.assertTrue(self.ddt.invoice_ids.fiscal_document_type_id.created_from_ddt)