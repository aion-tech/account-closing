from typing import Dict, List

import requests
from odoo import api, fields, models, Command
from .progress_logger import _logger

# _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
# _logger.info('Another transaction already locked documents rows. Cannot process documents.')

# __import__('pdb').set_trace() # SETTA UN PUNTO DI DEBUG
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
    "items_quant": {
        "method": "import_items_quant",
        "slug": "items",#uso lo stesso endpoint di items così sono sicuro di applicare l'inventario solo a quello che mi interessa
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
    "employees": {
        "method": "import_employees",
        "slug": "employees",
        "default": False,
    },
}


class MarcoImporter(models.TransientModel):
    _name = "marco.importer"
    _description = "Sommo Importatore di dati"
    select_all = fields.Boolean()  # default=True)
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
        _logger.warning("<--- INIZIO IMPORTAZIONE DI TUTTO --->")
        try:
            requests.get(BASE_URL, timeout=(2, 2))
        except:
            raise ValueError(f"Cannot reach the APIs")

        for key, value in IMPORT_METHOD_MAP.items():
            if self[key]:
                url = BASE_URL + value["slug"]
                try:
                    res = requests.get(url, timeout=(3, 10))
                    records = res.json()
                except:
                    raise ValueError(f"Cannot reach the APIs")
                getattr(self, value["method"])(records)
                self.env.cr.commit()

        _logger.warning("<--- IMPORTAZIONE COMPLETATA --->")

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
