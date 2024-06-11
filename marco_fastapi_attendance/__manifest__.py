{
    "name": "marco_fastapi_attendance",
    "summary": "",
    "description": "",
    "author": "Aion Tech Srl",
    "website": "https://aion-tech.it/",
    # https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": [
        "fastapi",
        "auth_api_key",
        "hr_attendance",
    ],
    "data": [
        "data/marco_fastapi_data.xml",
        "security/ir_rule+acl.xml",
        "security/ir.model.access.csv",
    ],
}
