from odoo.exceptions import ValidationError
from odoo.tests.common import tagged, TransactionCase

@tagged('post_install', '-at_install', 'marco')
class TestFiscalDocumentType(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestFiscalDocumentType, cls).setUpClass()
        cls.fiscal_document_type = cls.env["fiscal.document.type"].create({
            "code": "test",
            "name": "Test",
            "out_invoice": True,
            "in_invoice": False,
            "out_refund": False,
            "in_refund": False,
            "created_from_ddt":True,
            "priority": 1,
        })

    def test_fiscal_document_type_created_from_ddt1(self):
        with self.assertRaises(ValidationError):
            self.env["fiscal.document.type"].create({
                "code": "test2",
                "name": "Test2",
                "out_invoice": True,
                "in_invoice": False,
                "out_refund": False,
                "in_refund": False,
                "created_from_ddt":True,
                "priority": 1,
            })

    def test_fiscal_document_type_created_from_ddt2(self):
        fdt2 = self.env["fiscal.document.type"].create({
            "code": "test3",
            "name": "Test3",
            "out_invoice": True,
            "in_invoice": False,
            "out_refund": False,
            "in_refund": False,
            "created_from_ddt":False,
            "priority": 1,
        })
        # self.assertTrue(True)
        self.assertEqual(fdt2.created_from_ddt, False)
        with self.assertRaises(ValidationError):
            fdt2.created_from_ddt = True

