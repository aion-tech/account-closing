{
    "name": "marco_importer",
    "summary": "",
    "description": "Applicazione per importare i dati MARCO S.p.A.",
    "author": "MARCO S.p.A.",
    "website": "https://www.marco.it/",
    # https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "contacts",
        "base_vat",
        "uom",
        "stock",
        "purchase",
        "mrp",
        "sale_management",
        'sale_triple_discount',
        "web_notify",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/actions.xml",
        "views/menus.xml",
    ],
}
