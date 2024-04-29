from typing import Dict, List

import requests
from odoo import api, fields, models, Command
from .progress_logger import _logger

# _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
# _logger.info('Another transaction already locked documents rows. Cannot process documents.')

# __import__('pdb').set_trace() # SETTA UN PUNTO DI DEBUG
BASE_URL = "https://api.marco.it/odoo/"

IMPORT_METHOD_MAP = {
    "partners": {"method": "import_partners", "slug": "partners"},
    "items": {"method": "import_items", "slug": "items"},
    "bom_heads": {"method": "import_bom_heads", "slug": "bom/head"},
    "bom_components": {"method": "import_bom_components", "slug": "bom/component"},
    "workcenters": {"method": "import_workcenters", "slug": "bom/workcenter"},
    "bom_operations": {"method": "import_bom_operations", "slug": "bom/operation"},
    "suppliers_pricelists": {
        "method": "import_suppliers_pricelists",
        "slug": "supplier/pricelist",
    },
    "orders": {"method": "import_orders", "slug": "order"},
    "banks":{"method":"import_banks","slug":"banks"},
    "partners_bank":{"method":"import_partners_bank","slug":"partners/bank"},
}


class MarcoImporter(models.TransientModel):
    _name = "marco.importer"
    _description="Sommo Importatore di dati"
    select_all = fields.Boolean()#default=True)
    first_select_all_change= fields.Boolean(default=True)
    @api.onchange("select_all")
    def select_all_change(self):
        print(self.first_select_all_change)
        if self.first_select_all_change:
            self.first_select_all_change=False
            print(" ************ FIRST SELECT ALL CHANGE ************ ")
            return
        for key, value in IMPORT_METHOD_MAP.items():
            self[key] = self.select_all


    def import_all_data(self):
        _logger.warning("<--- INIZIO IMPORTAZIONE DI TUTTO --->")
        for key, value in IMPORT_METHOD_MAP.items():
            if self[key]:
                url = BASE_URL + value["slug"]
                try:
                    res = requests.get(url)
                    records = res.json()
                except:
                    raise ValueError(f"Cannot reach the APIs")
                getattr(self, value["method"])(records)
                self.env.cr.commit()

        _logger.warning("<--- IMPORTAZIONE COMPLETATA --->")

    def on_change_check(self,condition:bool=False,title:str="Errore:",message:str="Errore Generico",type:str="notification",level:str="warning"):
        
        if not self.first_select_all_change and condition:
            return {
                level: {
                    "title": title,
                    "message": message,
                    "type": type,
                },
            }