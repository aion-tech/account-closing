from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    banks = fields.Boolean()

    def import_banks(self, records):
        _logger.warning("<--- IMPORTAZIONE BANCHE INIZIATA --->")
        for idx, rec in enumerate(records):
            
            vals = {
                "bic": rec["bic"],
                "city": rec["city"],
                "country": rec["country"],
                "email": rec["email"],
                "name": rec["name"],
                "phone": rec["phone"],
                "state": rec["state"],
                "street": rec["street"],
                "zip": rec["zip"],
            }
            bank_id = self.env["res.bank"].search(
                [("name", "=", rec["name"])]
            )
            if workcenter_id:
                workcenter_id.write(vals)
            else:
                workcenter_id = self.env["mrp.workcenter"].create(vals)
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=workcenter_id and workcenter_id.code,
            )
        _logger.warning("<--- IMPORTAZIONE BANCHE TERMINATA --->")
