from odoo import api, fields, models, Command
from .progress_logger import _progress_logger, _logger


class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    bom_heads = fields.Boolean()

    @api.onchange("bom_heads")
    def bom_heads_change(self):
        return self.on_change_check(
            condition=self.bom_heads and not self.items,
            title="DIPENDENZA NELL'IMPORT",
            message="Le BOM_HEADS dipendono dagli ITEMS, assicurati di averli già importati.",
        )

    def import_bom_heads(self, records):
        _logger.warning("<--- IMPORTAZIONE BOM HEADS INIZIATA --->")

        for idx, rec in enumerate(records):
            product = self.env["product.template"].search(
                [("default_code", "=", rec["bom"])]
            )
            bom = False
            if product:
                bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", product.id)])

                if rec["outsourced"]:
                    partner_id = self.env["res.partner"].search(
                        [("ref", "=", rec["realSupplier"])]
                    )
                    vals = {
                        "product_tmpl_id": product.id,
                        "type": "subcontract",
                        "subcontractor_ids": partner_id
                        and [Command.set([partner_id.id])],
                    }
                    if bom:
                        bom.write(vals)
                    else:
                        bom = self.env["mrp.bom"].create(vals)
                else:
                    vals = {
                        "product_tmpl_id": product.id,
                        "type": rec["type"],
                    }
                    if bom:
                        bom.write(vals)
                    else:
                        bom = self.env["mrp.bom"].create(vals)
            _progress_logger(
                iterator=idx, all_records=records, additional_info=bom and product.name
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")
