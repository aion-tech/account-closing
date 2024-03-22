from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    bom_components = fields.Boolean()
    
    def import_bom_components(self, records):
        for idx, rec in enumerate(records):
            bom_product = self.env["product.template"].search(
                [("default_code", "=", rec["bom"])]
            )
            bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", bom_product.id)])

            component_product = self.env["product.product"].search(
                [("default_code", "=", rec["component"])]
            )
            # Se la bom padre è di natura subcontract devo aggiungere alle rotte del figlio la rotta Resupply Subcontractor on Order
            if bom.type == "subcontract":
                resupply_subcontractor_on_order = self.env.ref(
                    "mrp_subcontracting.route_resupply_subcontractor_mto"
                )

                component_product.route_ids = [
                    Command.link(resupply_subcontractor_on_order.id)
                ]

            if bom_product and component_product and bom:
                bom_line = self.env["mrp.bom.line"].search(
                    [("product_id", "=", component_product.id), ("bom_id", "=", bom.id)]
                )
                vals = {
                    "bom_id": bom.id,
                    "product_id": component_product.id,
                    "product_qty": rec["qty"],
                }
                if bom_line:
                    bom_line.write(vals)
                else:
                    bom_line = self.env["mrp.bom.line"].create(vals)

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=component_product and component_product.name,
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")
