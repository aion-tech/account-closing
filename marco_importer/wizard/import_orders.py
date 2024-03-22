from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger
from datetime import datetime

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    orders = fields.Boolean()

    def import_orders(self, records):
        _logger.warning("<--- IMPORTAZIONE ORDERS HEAD INIZIATA --->")
        for idx, rec in enumerate(records["heads"]):
            customer_id = self.env["res.partner"].search(
                [("ref", "=", rec["Customer"])]
            )
            if not customer_id:
                print(rec["Customer"], customer_id)
                continue
            vals = {
                "origin": rec["InternalOrdNo"],
                "commitment_date": datetime.strptime(
                    str(rec["ConfirmedDeliveryDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "date_order": datetime.strptime(
                    str(rec["OrderDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "partner_id": customer_id.id,
                "client_order_ref": rec["YourReference"],
                "picking_policy": "one",
            }
            order_head_id = self.env["sale.order"].search(
                [("origin", "=", rec["InternalOrdNo"])]
            )
            if order_head_id:
                order_head_id.write(vals)
            else:
                order_head_id = self.env["sale.order"].create(vals)
            
            for line_idx,line_rec in enumerate(records["lines"]):
                product_template_id = self.env["product.product"].search(
                    [("default_code", "=", line_rec["Item"])]
                )
                if not (product_template_id and order_head_id.origin==line_rec["InternalOrdNo"]):
                    if order_head_id.origin==line_rec["InternalOrdNo"]:
                        break
                    continue
                vals = {
                    "order_id": order_head_id.id,
                    "product_id": product_template_id.id,
                    "name": product_template_id.name,
                    "product_uom_qty": float(line_rec["Qty"]),
                    "price_unit": float(line_rec["UnitValue"]),
                    "sequence": line_rec["Position"],
                    "customer_lead": float(0),
                }
                order_line_id = self.env["sale.order.line"].search(
                    [
                        ("order_id", "=", order_head_id.id),
                        ("product_id", "=", product_template_id.id),
                        ("sequence", "=", line_rec["Position"]),
                    ]
                )
                if order_line_id:
                    order_line_id.write(vals)
                else:
                    order_line_id = self.env["sale.order.line"].create(vals)
                del records["lines"][line_idx]
                print(len(records["lines"]))
            order_head_id.action_confirm()
            _progress_logger(
                iterator=idx,
                all_records=records["heads"],
                additional_info=order_head_id and order_head_id.origin,
            )
        _logger.warning("<--- IMPORTAZIONE ORDERS HEAD TERMINATA --->")

