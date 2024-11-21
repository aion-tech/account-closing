{
    "name": "marco_mail_cleaner_llm",
    "summary": "",
    "description": "",
    "author": "MARCO S.p.A.,Carpikes",
    "website": "https://aion-tech.it/",
    # https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Uncategorized",
    "version": "16.0.1.0.1",
    "depends": [
        "base",
        "mail",
        "crm",
        "queue_job",
    ],
    'data': [
    'views/res_config_settings_view.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "marco_mail_cleaner_llm/static/src/components/message/message.xml",
            "marco_mail_cleaner_llm/static/src/models/*.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
