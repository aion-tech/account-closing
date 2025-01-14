# Copyright 2014-2022 ACSONE SA/NV (http://acsone.eu)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# Copyright 2016-2022 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2025 Federico Medici, Simone Rubino - Aion Tech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import time
from datetime import date

from odoo import fields
from odoo.tests.common import TransactionCase


class TestCutoffPrepaid(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.inv_model = cls.env["account.move"]
        cls.cutoff_model = cls.env["account.cutoff"]
        cls.account_model = cls.env["account.account"]
        cls.journal_model = cls.env["account.journal"]
        cls.main_company = cls.env.ref("base.main_company")
        cls.account_expense = cls.account_model.create(
            {
                "account_type": "expense",
                "company_id": cls.main_company.id,
                "name": "Test expense",
                "code": "TE.1",
            }
        )
        cls.account_payable = cls.account_model.create(
            {
                "account_type": "liability_payable",
                "company_id": cls.main_company.id,
                "name": "Test payable",
                "code": "TP.1",
            }
        )
        cls.account_cutoff = cls.account_model.create(
            {
                "account_type": "liability_current",
                "company_id": cls.main_company.id,
                "name": "Test cutoff",
                "code": "TC.1",
            }
        )
        cls.cutoff_journal = cls.journal_model.create(
            {
                "name": "Cutoff journal",
                "type": "general",
                "code": "GEN",
                "company_id": cls.main_company.id,
            }
        )
        cls.purchase_journal = cls.journal_model.create(
            {
                "name": "Purchase journal",
                "type": "purchase",
                "code": "PUR",
                "company_id": cls.main_company.id,
            }
        )

    def _date(self, date):
        """convert MM-DD to current year date YYYY-MM-DD"""
        return time.strftime("%Y-" + date)

    def _days(self, start_date, end_date):
        start_date = fields.Date.from_string(self._date(start_date))
        end_date = fields.Date.from_string(self._date(end_date))
        return (end_date - start_date).days + 1

    def _create_invoice(self, date, amount, start_date, end_date):
        invoice = self.inv_model.create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "invoice_date": self._date(date),
                "date": self._date(date),
                "partner_id": self.env.ref("base.res_partner_2").id,
                "journal_id": self.purchase_journal.id,
                "move_type": "in_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "expense",
                            "price_unit": amount,
                            "quantity": 1,
                            "account_id": self.account_expense.id,
                            "start_date": self._date(start_date),
                            "end_date": self._date(end_date),
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        self.assertEqual(amount, invoice.amount_untaxed)
        return invoice

    def _create_cutoff(self, date, cutoff_type="prepaid_expense"):
        cutoff = self.cutoff_model.create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "cutoff_date": self._date(date),
                "cutoff_type": "prepaid_expense",
                "cutoff_journal_id": self.cutoff_journal.id,
                "cutoff_account_id": self.account_cutoff.id,
                "source_journal_ids": [(6, 0, [self.purchase_journal.id])],
            }
        )
        return cutoff

    def test_with_cutoff_before_after_and_in_the_middle(self):
        """basic test with cutoff before, after and in the middle"""
        amount = self._days("04-01", "06-30")
        amount_2months = self._days("05-01", "06-30")
        # invoice to be spread of 3 months
        self._create_invoice("01-15", amount, start_date="04-01", end_date="06-30")
        # cutoff after one month of invoice period -> 2 months cutoff
        cutoff = self._create_cutoff("04-30")
        cutoff.get_lines()
        self.assertEqual(amount_2months, cutoff.total_cutoff_amount)
        # cutoff at end of invoice period -> no cutoff
        cutoff = self._create_cutoff("06-30")
        cutoff.get_lines()
        self.assertEqual(0, cutoff.total_cutoff_amount)
        # cutoff before invoice period -> full value cutoff
        cutoff = self._create_cutoff("01-31")
        cutoff.get_lines()
        self.assertEqual(amount, cutoff.total_cutoff_amount)

    def tests_1(self):
        """generate move, and test move lines grouping"""
        # two invoices
        amount = self._days("04-01", "06-30")
        self._create_invoice("01-15", amount, start_date="04-01", end_date="06-30")
        self._create_invoice("01-16", amount, start_date="04-01", end_date="06-30")
        # cutoff before invoice period -> full value cutoff
        cutoff = self._create_cutoff("01-31")
        cutoff.get_lines()
        cutoff.create_move()
        self.assertEqual(amount * 2, cutoff.total_cutoff_amount)
        self.assertTrue(cutoff.move_id, "move not generated")
        # two invoices, but two lines (because the two cutoff lines
        # have been grouped into one line plus one counterpart)
        self.assertEqual(len(cutoff.move_id.line_ids), 2)

    def test_general_entry_prepaid_expense_cutoff_account(self):
        """
        Create an account move on a general journal for an expense account,
        only the expense cutoff should retrieve its line."""
        # Arrange
        company = self.env.ref("base.main_company")
        bank_account = self.env["account.account"].search(
            [
                ("account_type", "=", "asset_cash"),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        expense_account = self.account_expense
        misc_journal = self.cutoff_journal
        month_day_move_date = "10-31"
        move_date = fields.Date.from_string(self._date(month_day_move_date))

        # Create the move directly
        move = self.env["account.move"].create(
            {
                "date": move_date,
                "journal_id": misc_journal.id,
                "company_id": company.id,
                "move_type": "entry",
            }
        )

        # Add lines to the move
        move.write(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": expense_account.id,
                            "debit": 1000,
                            "start_date": date(move_date.year + 1, 1, 1),
                            "end_date": date(move_date.year + 1, 12, 31),
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": bank_account.id,
                            "credit": 1000,
                        },
                    ),
                ]
            }
        )

        # Post the move
        move.action_post()

        # Create the cutoff entries, checking if they already exist
        cutoff_date = move_date.replace(month=10, day=31)  # Fixing the date format
        cutoff_date = self._date(cutoff_date)
        prepaid_expense_cutoff = self.env["account.cutoff"].search(
            [
                ("cutoff_date", "=", cutoff_date),
                ("company_id", "=", company.id),
                ("cutoff_type", "=", "prepaid_expense"),
            ],
            limit=1,
        )

        if not prepaid_expense_cutoff:
            prepaid_expense_cutoff = self._create_cutoff(
                cutoff_date,
                cutoff_type="prepaid_expense",
            )
            prepaid_expense_cutoff.source_journal_ids = misc_journal

        prepaid_revenue_cutoff = self.env["account.cutoff"].search(
            [
                ("cutoff_date", "=", cutoff_date),
                ("company_id", "=", company.id),
                ("cutoff_type", "=", "prepaid_revenue"),
            ],
            limit=1,
        )

        if not prepaid_revenue_cutoff:
            prepaid_revenue_cutoff = self._create_cutoff(
                cutoff_date,
                cutoff_type="prepaid_revenue",
            )
            prepaid_revenue_cutoff.source_journal_ids = misc_journal

        # pre-condition
        expense_move_line = move.line_ids.filtered(
            lambda line: line.account_id.internal_group == "expense"
        )
        self.assertTrue(expense_move_line)
        self.assertEqual(move.journal_id.type, "general")

        self.assertEqual(prepaid_expense_cutoff.cutoff_type, "prepaid_expense")
        self.assertEqual(prepaid_expense_cutoff.source_journal_ids.type, "general")

        self.assertEqual(prepaid_revenue_cutoff.cutoff_type, "prepaid_revenue")
        self.assertEqual(prepaid_revenue_cutoff.source_journal_ids.type, "general")

        # Act
        prepaid_expense_cutoff.get_lines()
        prepaid_revenue_cutoff.get_lines()

        # Assert
        self.assertEqual(
            prepaid_expense_cutoff.line_ids.origin_move_line_id, expense_move_line
        )
        self.assertFalse(prepaid_revenue_cutoff.line_ids)
