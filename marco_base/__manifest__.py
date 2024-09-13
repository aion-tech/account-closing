{
    "name": "marco_base",
    "summary": "",
    "description": "",
    "author": "MARCO S.p.A.",
    "website": "https://www.marco.it/",
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
       # "l10n_generic_auto_transfer_demo",
       # "l10n_generic_coa",
        
        "marco_maintenance",
        "microsoft_account",
        "microsoft_calendar",
        "microsoft_outlook",
        "partner_firstname",
        "report_xml",
        "sale_project_stock",
        "websocket_refresh",
        "marco_importer",
        "mrp_subcontracting",
        "mrp_multi_level",
        "server_action_mass_edit" #modulo per la modifica massiva
    ],
    "data": [
       
        # security/ir.model.access.csv,
        # "views/views.xml",
    ],
    "post_init_hook":"marco_post_init_hook",
    "installable": True,
}
