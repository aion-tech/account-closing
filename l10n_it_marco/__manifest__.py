# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Italy - Accounting - MARCO S.p.A.',
    'version': '0.6',
    'depends': [
        'account',
        'base_iban',
        'base_vat',
    ],
    'author': 'OpenERP Italian Community, MARCO S.p.A.',
    'description': """
Piano dei conti italiano della MARCO S.p.A. .
================================================

Italian accounting chart and localization.
    """,
    'category': 'Accounting/Localizations/Account Charts',
    'website': 'http://www.odoo.com/',
    'data': [
        'data/account_account_tag.xml',
        'data/account_chart_template.xml',
        'data/account.account.template.xml',
        
        'data/account_chart_template_accounts.xml',
        'data/account.tax.group.csv',
        'data/account_tax_report_data.xml',
        'data/account_tax_template.xml',
        'data/account.fiscal.position.template.csv',
        'data/account_fiscal_position_tax_template_data.xml',
        'data/account_chart_template_data.xml',
        'data/report_invoice.xml'
    ],
    'demo': [
        'demo/demo_company.xml',
    ],
    'license': 'LGPL-3',
}
