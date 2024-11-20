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
    },
    "items": {
        "method": "import_items",
        "slug": "items",
        "default": False,
    },
    "bom_heads": {
        "method": "import_bom_heads",
        "slug": "bom/head",
        "default": False,
    },
    "workcenters": {
        "method": "import_workcenters",
        "slug": "bom/workcenter",
        "default": False,
    },
    "bom_operations": {
        "method": "import_bom_operations",
        "slug": "bom/operation",
        "default": False,
    },
    "bom_components": {
        "method": "import_bom_components",
        "slug": "bom/component",
        "default": False,
    },
    "suppliers_pricelists": {
        "method": "import_suppliers_pricelists",
        "slug": "supplier/pricelist",
        "default": False,
    },
    "orders": {
        "method": "import_orders",
        "slug": "order",
        "default": False,
    },
    "purchase_orders": {
        "method": "import_purchase_orders",
        "slug": "orders/purchase",
        "default": False,
    },
    "banks": {
        "method": "import_banks",
        "slug": "banks",
        "default": False,
    },
    "partners_bank": {
        "method": "import_partners_bank",
        "slug": "partners/bank",
        "default": False,
    },
    "items_quant": {
        "method": "import_items_quant",
        "slug": "items",
        "default": False,
    },
    "employees": {
        "method": "import_employees",
        "slug": "employees",
        "default": False,
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
        # Esegui l'importazione in background con `with_delay`
        self.env.user.notify_info(message="Importazione aggiunta alla coda ...")
        self.with_delay(priority=1,description="MARCO IMPORTER: Import from widget").run_import_all_data()

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
        """Wrapper per eseguire import_data come job di queue_job"""
        self.with_delay(priority=1,max_retries=2,description=f"MARCO IMPORTER: {model_name}").import_data(model_name)
        _logger.warning("<--- IMPORTAZIONE COMPLETATA --->")


    def import_data(self, model_name: str):
        """Metodo generico per importare i dati di un modello specificato."""
        model_config = IMPORT_METHOD_MAP.get(model_name)
        if not model_config:
            self.env.user.notify_danger(message=f"Modello '{model_name}' non trovato in IMPORT_METHOD_MAP.")
            return
        
        # Costruisce l'URL per il modello specifico
        url = BASE_URL + model_config["slug"]
        try:
            response = requests.get(url, timeout=(3, 10))
            records = response.json()
        except requests.RequestException as e:
            self.env.user.notify_danger(message=f"Errore nel recupero dei dati per '{model_name}': {e}")
            return
        
        # Recupera il metodo di importazione specifico
        import_method = getattr(self, model_config["method"], None)
        if import_method:
            import_method(records)
            self.env.cr.commit()
            _logger.info(f"Importazione completata per '{model_name}'.")
            self.env.user.notify_success(message=f"Importazione completata per '{model_name}'.")
        else:
            self.env.user.notify_danger(message=f"Metodo di importazione '{model_config['method']}' non trovato per '{model_name}'.")

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
