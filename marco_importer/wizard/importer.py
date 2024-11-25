from typing import Dict, List
import requests
from odoo import api, fields, models, Command
from .progress_logger import _logger
from datetime import datetime

BASE_URL = "https://api.marco.it/odoo/"

IMPORT_METHOD_MAP = {
    "partners": {
        "method": "import_partners",
        "slug": "partners",
        "default": False,
        "dependencies": ["l10n_it_marco_extra"],
    },
    "items": {
        "method": "import_items",
        "slug": "items",
        "default": False,
        "dependencies": ["l10n_it_marco_extra"],
    },
    "bom_heads": {
        "method": "import_bom_heads",
        "slug": "bom/head",
        "default": False,
        "dependencies": [""],
    },
    "workcenters": {
        "method": "import_workcenters",
        "slug": "bom/workcenter",
        "default": False,
        "dependencies": [""],
    },
    "bom_operations": {
        "method": "import_bom_operations",
        "slug": "bom/operation",
        "default": False,
        "dependencies": [""],
    },
    "bom_components": {
        "method": "import_bom_components",
        "slug": "bom/component",
        "default": False,
        "dependencies": [""],
    },
    "suppliers_pricelists": {
        "method": "import_suppliers_pricelists",
        "slug": "supplier/pricelist",
        "default": False,
        "dependencies": [""],
    },
    "orders": {
        "method": "import_orders",
        "slug": "order",
        "default": False,
        "dependencies": [""],
    },
    "purchase_orders": {
        "method": "import_purchase_orders",
        "slug": "orders/purchase",
        "default": False,
        "params": {"include_delivered": False},
        "dependencies": [""],
    },
     "purchase_orders_include_delivered": {
        "method": "import_purchase_orders",
        "slug": "orders/purchase",
        "default": False,
        "params": {"include_delivered": True},
        "dependencies": [""],
    },
    "banks": {
        "method": "import_banks",
        "slug": "banks",
        "default": False,
        "dependencies": ["l10n_it_marco_extra"],
    },
    "partners_bank": {
        "method": "import_partners_bank",
        "slug": "partners/bank",
        "default": False,
        "dependencies": [""],
    },
    "items_quant": {
        "method": "import_items_quant",
        "slug": "items",
        "default": False,
        "dependencies": [""],
    },
    "employees": {
        "method": "import_employees",
        "slug": "employees",
        "default": False,
        "dependencies": [""],
    },
}

class MarcoImporter(models.TransientModel):
    _name = "marco.importer"
    _description = "Sommo Importatore di dati"

    select_all = fields.Boolean()
    first_select_all_change = fields.Boolean(default=True)

    @api.onchange("select_all")
    def select_all_change(self):
        if self.first_select_all_change:
            self.first_select_all_change = False
            _logger.warning("************ FIRST SELECT ALL CHANGE ************ ")
            for key, value in IMPORT_METHOD_MAP.items():
                self[key] = value["default"]
                _logger.warning(f"default={value['default']}  -->  {key} ")
            return
        for key, value in IMPORT_METHOD_MAP.items():
            self[key] = self.select_all

    def import_all_data(self):
        self.env.user.notify_info(message="Importazione aggiunta alla coda ...")
        self.with_delay(priority=1, description="MARCO IMPORTER: Import from widget").run_import_all_data()

    def run_import_all_data(self):
        _logger.warning("<--- INIZIO IMPORTAZIONE DI TUTTO --->")
        try:
            requests.get(BASE_URL, timeout=(2, 2))
        except requests.RequestException:
            self.env.user.notify_danger(message="Errore: impossibile raggiungere le API.")
            return
        self.env.user.notify_info(message="Importazione iniziata.")
        for key in IMPORT_METHOD_MAP:
            if self[key]:
                self.import_data_in_background(key)

    def import_data_in_background(self, model_name: str):
        self.with_delay(priority=1, max_retries=2, description=f"MARCO IMPORTER: {model_name}").import_data(model_name)
        _logger.warning("<--- IMPORTAZIONE COMPLETATA --->")

    def import_data(self, model_name: str):
        model_config = IMPORT_METHOD_MAP.get(model_name)
        if not model_config:
            self.env.user.notify_danger(message=f"Modello '{model_name}' non trovato in IMPORT_METHOD_MAP.")
            return

        # Controllo e installazione delle dipendenze
        dependencies = model_config.get("dependencies", [])
        self.ensure_dependencies_installed(dependencies)

        # Costruisce l'URL per il modello specifico
        url = BASE_URL + model_config["slug"]
        try:
            response = requests.get(url, timeout=(3, 10))
            records = response.json()
        except requests.RequestException as e:
            self.env.user.notify_danger(message=f"Errore nel recupero dei dati per '{model_name}': {e}")
            return

        import_method = getattr(self, model_config["method"], None)
        if import_method:
            params = model_config.get("params", {})
            import_method(records, **params)
            self.env.cr.commit()
            _logger.info(f"Importazione completata per '{model_name}'.")
            self.env.user.notify_success(message=f"Importazione completata per '{model_name}'.")
        else:
            self.env.user.notify_danger(message=f"Metodo di importazione '{model_config['method']}' non trovato per '{model_name}'.")

    def ensure_dependencies_installed(self, dependencies: List[str]):
        module_model = self.env['ir.module.module']
        for module_name in dependencies:
            module = module_model.search([('name', '=', module_name)], limit=1)
            if module and module.state not in ('installed', 'to install'):
                module.button_immediate_install()
                self.env.cr.commit()
                _logger.info(f"Modulo '{module_name}' installato correttamente.")

    def install_italian_oca_localization(self):
        module_model = self.env['ir.module.module']

        l10n_it_marco_extra = module_model.search([('name', '=', 'l10n_it_marco_extra')], limit=1)
        if l10n_it_marco_extra and l10n_it_marco_extra.state not in ('installed', 'to install'):
            l10n_it_marco_extra.button_immediate_install()
            self.env.cr.commit()  # Commit necessario

        # Disinstalla il modulo account_asset
        account_asset_module = module_model.search([('name', '=', 'account_asset')], limit=1)
        if account_asset_module and account_asset_module.state == 'installed':
            account_asset_module.button_immediate_uninstall()
            self.env.cr.commit()  # Commit necessario
       
        # Procedi con l'installazione di l10n_it_asset_management solo se account_asset è disinstallato
        asset_management_module = module_model.search([('name', '=', 'l10n_it_asset_management')], limit=1)
        if asset_management_module and asset_management_module.state not in ('installed', 'to install'):
            if account_asset_module.state == 'installed':
                self.env.user.notify_error(message="Impossibile installare l10n_it_asset_management, account_asset è ancora installato.")
                return
            asset_management_module.button_immediate_install()
            self.env.cr.commit()  # Commit necessario

    def on_change_check(
        self,
        condition: bool = False,
        title: str = "Errore:",
        message: str = "Errore Generico",
        type: str = "notification",
        level: str = "warning",
    ):
        if not self.first_select_all_change and condition:
            return {
                level: {
                    "title": title,
                    "message": message,
                    "type": type,
                },
            }
