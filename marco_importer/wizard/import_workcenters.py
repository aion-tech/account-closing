from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    workcenters = fields.Boolean()

    def import_workcenters(self, records):
        _logger.warning("<--- IMPORTAZIONE WORKCENTERS INIZIATA --->")
        for idx, rec in enumerate(records):
            if rec["Outsourced"] == "1":
                continue
            vals = {
                "name": rec["name"],
                "code": rec["code"],
                "costs_hour": rec["costs_hour"],
                "note": rec["note"],
            }
            workcenter_id = self.env["mrp.workcenter"].search(
                [("code", "=", rec["code"])]
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
        _logger.warning("<--- IMPORTAZIONE WORKCENTERS TERMINATA --->")
