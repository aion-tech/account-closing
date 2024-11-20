# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Italy - Accounting Extra - MARCO S.p.A.",
    "version": "0.6",
    "depends": [
        "l10n_it_marco",
        #"l10n_it_asset_management",
    ],
    "author": "MARCO S.p.A.",
    "description": """
Piano dei conti italiano della MARCO S.p.A. .
================================================

Italian accounting chart and localization.
    """,
    "category": "Accounting/Localizations/Account Charts",
    "website": "http://www.odoo.com/",
    "data": [
        "data/partners.xml",
        "data/account_tax_records.xml",
        "data/account_tax_records_cpa.xml",
        "data/account_journal.xml",
        "data/date_range_type.xml",
        "data/account_rc_type.xml",
        "data/payment_terms.xml",
        "data/withholding_tax.xml",
        "data/account_fiscal_position_extra.xml",
        "data/riba_configuration.xml",
    ],
    "post_init_hook": "marco_post_init_hook",
    "license": "LGPL-3",
}
