{
    "name": "marco_importer",
    "summary": "",
    "description": "",
    "author": "Aion Tech Srl",
    "website": "https://aion-tech.it/",
    # https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/actions.xml",
        "views/menus.xml",
    ],
}
