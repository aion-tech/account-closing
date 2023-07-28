# Copyright 2023 Sergio Corato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("-at_install", "post_install")
class TestInvoiceStartEndDates(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.inv_model = cls.env["account.move"]
        cls.account_model = cls.env["account.account"]
        cls.journal_model = cls.env["account.journal"]
        cls.account_revenue = cls.account_model.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )
        cls.sale_journal = cls.journal_model.search([("type", "=", "sale")], limit=1)
        cls.maint_product = cls.env.ref(
            "account_invoice_start_end_dates.product_maintenance_contract_demo"
        )
        cls.insur_product = cls.env.ref(
            "account_invoice_start_end_dates.product_insurance_contract_demo"
        )
        cls.product = cls.env.ref("product.product_product_5")
        cls.user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.group_accounting = cls.env.ref("account.group_account_user")
        cls.account_user = cls.user_model.create(
            [
                {
                    "name": "Accounting user",
                    "login": "account user",
                    "email": "account@email.it",
                    "groups_id": [
                        (4, cls.group_accounting.id),
                    ],
                }
            ]
        )
        cls.company = cls.account_user.company_id

    @staticmethod
    def _date(date):
        """convert MM-DD to current year date YYYY-MM-DD"""
        return time.strftime("%Y-" + date)

    def _test_invoice(self):
        apply_dates_all_lines = self.company.apply_dates_all_lines
        invoice = self.inv_model.create(
            {
                "date": self._date("01-01"),
                "partner_id": self.env.ref("base.res_partner_2").id,
                "journal_id": self.sale_journal.id,
                "move_type": "out_invoice",
                "start_date": self._date("03-01"),
                "end_date": self._date("05-31"),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.maint_product.id,
                            "name": "Maintenance IPBX 12 mois",
                            "price_unit": 2400,
                            "quantity": 1,
                            "account_id": self.account_revenue.id,
                            "start_date": self._date("01-01"),
                            "end_date": self._date("12-31"),
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.insur_product.id,
                            "name": "Maintenance téléphones 12 mois",
                            "price_unit": 12,
                            "quantity": 10,
                            "account_id": self.account_revenue.id,
                            "start_date": False,
                            "end_date": False,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.maint_product.id,
                            "name": "Maintenance Fax 6 mois",
                            "price_unit": 120.75,
                            "quantity": 1,
                            "account_id": self.account_revenue.id,
                            "start_date": self._date("01-01"),
                            "end_date": self._date("06-30"),
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": "HD IPBX",
                            "price_unit": 215.5,
                            "quantity": 1,
                            "account_id": self.account_revenue.id,
                        },
                    ),
                ],
            }
        )
        # add line to test onchange
        line = (
            self.env["account.move.line"]
            .with_user(self.account_user)
            .with_context(check_move_validity=False)
            .create(
                {
                    "move_id": invoice.id,
                    "product_id": self.insur_product.id,
                    "name": "Insurance",
                    "price_unit": 100,
                    "quantity": 1,
                    "account_id": self.account_revenue.id,
                }
            )
        )
        line._onchange_product_id()
        line._convert_to_write(line._cache)
        invoice.action_post()

        for line in invoice.line_ids.filtered(
            lambda x: x.product_id == self.maint_product
        ):
            self.assertEqual(line.start_date.strftime("%Y-%m-%d"), self._date("01-01"))
        for line in invoice.line_ids.filtered(
            lambda x: x.product_id == self.insur_product
        ):
            self.assertEqual(line.start_date, invoice.start_date)
        for line in invoice.line_ids.filtered(lambda x: x.product_id == self.product):
            if not apply_dates_all_lines:
                self.assertFalse(line.start_date)
                self.assertFalse(line.end_date)
            else:
                self.assertEqual(line.start_date, invoice.start_date)
                self.assertEqual(line.end_date, invoice.end_date)
        invoice.line_ids[0].end_date = self._date("04-30")
        invoice.write({})
        self.assertEqual(
            invoice.line_ids[0].end_date.strftime("%Y-%m-%d"), self._date("04-30")
        )
        invoice.write({"end_date": self._date("04-15")})
        for line in invoice.line_ids.filtered(lambda x: x.product_id.must_have_dates):
            self.assertEqual(line.end_date.strftime("%Y-%m-%d"), self._date("04-15"))

    def test_01_invoice_without_apply_dates(self):
        self.company.apply_dates_all_lines = False
        self._test_invoice()

    def test_02_invoice_with_apply_dates(self):
        self.company.apply_dates_all_lines = True
        self._test_invoice()
