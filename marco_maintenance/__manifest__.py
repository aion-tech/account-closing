{
    "name": "marco_maintenance",
    "summary": "",
    "description": "",
    "author": "Aion Tech Srl",
    "website": "https://aion-tech.it/",
    # https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Uncategorized",
    "version": "16.0.1.0.1",
    "depends": [
        "maintenance",
        "documents",
        "websocket_refresh",
    ],
    "data": [
        "data/folder_data.xml",
        "views/maintenance_equipment_views.xml",
        "views/maintenance_request_views.xml",
    ],
}
