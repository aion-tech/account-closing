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
        "web_notify",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/folder_data.xml",
        "data/ir_sequence_data.xml",
        "views/maintenance_equipment_views.xml",
        "views/maintenance_request_views.xml",
        "views/maintenance_equipment_category_views.xml",
        "views/maintenance_request_template_views.xml",
    ],
}
