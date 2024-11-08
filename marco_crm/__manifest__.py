{
    'name': 'Marco CRM',
    "version": "16.0.1.0.0",
    'summary': 'Custom CRM module for Marco',
    'description': 'This module provides custom CRM functionalities for Marco.it',
    'author': 'Aion-Tech',
    "website": "https://aion-tech.it/",
    'category': 'Sales',
    'depends': [
        'base', 
        'crm',
        'contacts',
        'product',
        ],
    'data': [
        #security
        'security/ir.model.access.csv',
        #views
        'views/partner_type_views.xml',
        'views/partner_applicability_views.xml',
        'views/marco_crm_menus.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
}