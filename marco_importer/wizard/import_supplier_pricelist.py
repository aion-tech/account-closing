from odoo import api, fields, models, Command
from .progress_logger import _progress_logger, _logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    suppliers_pricelists = fields.Boolean()

    def import_suppliers_pricelists(self, records):
        _logger.warning("<--- IMPORTAZIONE SUPPLIER PRICELIST INIZIATA --->")
        
        # Rimuove tutti i listini esistenti prima di importare
        allPrices = self.env["product.supplierinfo"].search([])
        if allPrices:
            allPrices.unlink()

        for idx, record in enumerate(records):
            # Ottieni l'articolo principale
            item_code = record.get("Item")
            pricelists = record.get("pricelist", [])

            # Cerca il prodotto corrispondente
            product_id = self.env["product.template"].search([("default_code", "=", item_code)])

            imported_count = 0  # Conta i listini importati per questo articolo

            if product_id:
                for pricelist in pricelists:
                    # Cerca il fornitore corrispondente
                    supplier_id = self.env["res.partner"].search([("ref", "=", pricelist["Supplier"])])
                    
                    # Gestisci le date
                    date_start = (
                        pricelist["date_start"] != "1799-12-30T23:10:04.000Z" and pricelist["date_start"]
                    )
                    date_end = (
                        pricelist["date_end"] != "1799-12-30T23:10:04.000Z" and pricelist["date_end"]
                    )

                    if supplier_id:
                        # Crea il record del listino
                        vals = {
                            "product_tmpl_id": product_id.id,
                            "partner_id": supplier_id.id,
                            "date_start": date_start or False,
                            "date_end": date_end or False,
                            "price": pricelist["Price"],
                            "min_qty": pricelist["Qty"],
                            "delay": int(pricelist["DaysForDelivery"]),
                            "sequence": pricelist["sequence"],  # Include il campo sequence
                        }
                        self.env["product.supplierinfo"].create(vals)
                        imported_count += 1

            # Log per articolo usando _progress_logger
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=f"Articolo {item_code}: importati {imported_count} listini fornitori."
            )

        _logger.warning("<--- IMPORTAZIONE SUPPLIER PRICELIST TERMINATA --->")
