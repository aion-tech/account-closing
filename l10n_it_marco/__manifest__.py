# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Italy - Accounting - MARCO S.p.A.',
    'version': '0.6',
    'depends': [
        'account',
        'base_iban',
        'base_vat',
        'l10n_it_vat_registries',
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
        'data/account_account_template.xml',
        'data/account_account_template_manual.xml',
        'data/account_account_group.xml',    
        'data/account_chart_template_accounts.xml',     
        'data/account_chart_template_data.xml',
        'data/account_tax_registry.xml',
        
    ],
    'demo': [
       # 'demo/demo_company.xml',
    ],
    'license': 'LGPL-3',
}
