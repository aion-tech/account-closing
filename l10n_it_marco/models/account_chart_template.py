from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _load(self, company):
        """Set tax calculation rounding method required in Italian localization
        Also to avoid rounding errors when sent with FatturaPA"""
        res = super()._load(company)
        if company.account_fiscal_country_id.code == "IT":
            # Set tax calculation rounding method to 'round_globally' for Italian localization
            company.write({"tax_calculation_rounding_method": "round_globally"})
            
            # Search for the VAT split payment account with specific code '10DEIVPA'
            vat_split_payment_account = self.env["account.account"].search(
                [("company_id", "=", company.id), ("code", "=", "10DEIVPA")]
            )
            
            # Set the split payment tax group properties for receivable and payable accounts
            split_payment_tax_group = self.env.ref('l10n_it_split_payment.tax_group_split_payment').with_company(company)
            split_payment_tax_group.property_tax_receivable_account_id = vat_split_payment_account
            split_payment_tax_group.property_tax_payable_account_id = vat_split_payment_account

            # Set the default sale tax for Italian localization
            default_sale_tax = self.env.ref('l10n_it_marco.1_tax_22_sale')
            company.account_sale_tax_id = default_sale_tax

            # Set the default purchase tax for Italian localization
            default_purchase_tax = self.env.ref('l10n_it_marco.1_tax_22_purchase')
            company.account_purchase_tax_id = default_purchase_tax

            # Set the company's split payment account ID
            company.sp_account_id = vat_split_payment_account

        return res