from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    bom_operations = fields.Boolean()

    def import_bom_operations(self, records):
        _logger.warning("<--- IMPORTAZIONE OPERAZIONI INIZIATA --->")
        for idx, rec in enumerate(records):
            product_id = self.env["product.template"].search(
                [("default_code", "=", rec["bom"])]
            )
            if not product_id:
                continue

            bom_id = self.env["mrp.bom"].search(
                [("product_tmpl_id", "=", product_id.id)]
            )
            if not bom_id or bom_id.type == "subcontract":
                continue

            workcenter_id = self.env["mrp.workcenter"].search(
                [("code", "=", rec["wc_code"])]
            )

            if not workcenter_id:
                raise ValueError(f"WORKCENTER {rec['wc_code']} not found:{rec}")

            vals = {
                "name": rec["OperationDesc"],
                "bom_id": bom_id.id,
                "workcenter_id": workcenter_id.id,
                "time_mode": "manual",
                "time_cycle_manual": rec["time_cycle_manual"],
                "sequence": rec["RtgStep"],
                "note": rec["note"],
            }
            operation_id = self.env["mrp.routing.workcenter"].search(
                [
                    ("name", "=", rec["OperationDesc"]),
                    ("bom_id", "=", bom_id.id),
                    ("workcenter_id", "=", workcenter_id.id),
                ]
            )
            if operation_id:
                operation_id.write(vals)
            else:
                operation_id = self.env["mrp.routing.workcenter"].create(vals)

            _progress_logger(
                iterator=idx, all_records=records, additional_info=operation_id.name
            )
        _logger.warning("<--- IMPORTAZIONE OPERAZIONI TERMINATA --->")

