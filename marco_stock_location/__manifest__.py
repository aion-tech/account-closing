# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MARCO LOCATION',
    'version': '0.1',
    'depends': [
       'stock',
       'stock_barcode',
       'web_notify',
    ],
    'author': 'MARCO S.p.A.',
    'description': """
Piano dei conti italiano della MARCO S.p.A. .
================================================

Italian accounting chart and localization.
    """,
    'category': 'Uncategorize',
    'website': 'http://www.marco.it/',
    'data': [
       
        'data/wms_location.xml',
        'data/wms_location_CLAV.xml',
        'data/actions.xml',
        
    ],
    "post_init_hook":"marco_post_init_hook",
    'license': 'LGPL-3',
}
