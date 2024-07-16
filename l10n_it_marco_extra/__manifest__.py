# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Italy - Accounting - MARCO S.p.A.',
    'version': '0.6',
    'depends': [
        'account',
        'base_iban',
        'base_vat',
        'l10n_it_marco'
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
       
        'data/account_journal.xml',
        'data/date_range_type.xml',
        
    ],
    "post_init_hook":"marco_post_init_hook",
    'license': 'LGPL-3',
}
