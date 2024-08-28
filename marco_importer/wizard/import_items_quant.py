from odoo import api, fields, models, Command
from .progress_logger import _progress_logger, _logger


class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    items_quant = fields.Boolean()

    def import_items_quant(self, records):
        _logger.warning("<--- IMPORTAZIONE QUANTI INIZIATA --->")
        quants = self.env["stock.quant"]
        for idx, rec in enumerate(records):
            product_template_id = self.env["product.template"].search(
                [("default_code", "=", rec["default_code"])]
            )
            product_product_id = self.env["product.product"].search(
                [("product_tmpl_id", "=", product_template_id.id)]
            )
            if not product_template_id:
                continue
            # abbiamo commentato tutto per l'inventario, non voglio caricare la giacenza attuale di mago
            # gestione della giacenza di magazzino
            if product_template_id.detailed_type == "product" :

                warehouse = self.env["stock.warehouse"].search(
                    [("company_id", "=", self.env.company.id)], limit=1
                )
                quant = self.env["stock.quant"].with_context(inventory_mode=True).create(
                    {
                        "product_id": product_product_id.id,
                        "location_id": warehouse.lot_stock_id.id,
                        "inventory_quantity": rec[
                            "bookInv"
                        ],  # if rec["bookInv"] and rec["bookInv"] > 0 else 0,# ignoro tutti i negativi e imposto a 0 la quantità
                    }
                )
                quants |= quant

            product_mrp_area = self.env["product.mrp.area"].search(
                [("product_id", "=", product_product_id.id)]
            )
            vals = {
                "mrp_area_id": self.env.ref("mrp_multi_level.mrp_area_stock_wh0").id,
                "product_id": product_product_id.id,
                "location_proc_id": self.env.ref("stock.stock_location_stock").id,
                "mrp_nbr_days": 14,
                # finchè proviamo l'mrp questo lo lasciamo commentato perchè se no crea ordini di produzione per ripristinare le scorte di sicurezza
                # "mrp_minimum_stock":rec["minimumStock"],
                # "mrp_qty_multiple":rec["reorderingLotSize"]
            }
            if product_mrp_area:
                product_mrp_area.write(vals)
            else:
                product_mrp_area = self.env["product.mrp.area"].create(vals)

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=f'{product_template_id.default_code} = {rec["bookInv"]}',
            )
        _logger.warning( f"<--- APPLICO I QUANTI A {str(len(quants))} PRODOTTI --->")
        # Ora chiamiamo `action_apply_inventory` una sola volta su tutti i `stock.quant`
        if quants:
            quants.action_apply_inventory()
        _logger.warning("<--- IMPORTAZIONE QUANTI TERMINATA --->")
