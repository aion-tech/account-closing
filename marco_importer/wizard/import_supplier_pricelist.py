from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    suppliers_pricelists = fields.Boolean()

    def import_suppliers_pricelists(self, records):
        _logger.warning("<--- IMPORTAZIONE SUPPLIER PRICELIST INIZIATA --->")
        allPrices = self.env["product.supplierinfo"].search([])
        if allPrices:
            allPrices.unlink()
        for idx, rec in enumerate(records):

            product_id = self.env["product.template"].search(
                [("default_code", "=", rec["Item"])]
            )
            supplier_id = self.env["res.partner"].search(
                [("ref", "=", rec["Supplier"])]
            )
            date_start = str(rec["date_start"]) != "1799-12-30T23:10:04.000Z" and str(
                rec["date_start"]
            )
            date_end = str(rec["date_end"]) != "1799-12-30T23:10:04.000Z" and str(
                rec["date_end"]
            )
            if product_id and supplier_id:
                vals = {
                    "product_tmpl_id": product_id.id,
                    "partner_id": supplier_id.id,
                    "date_start": date_start,
                    "date_end": date_end,
                    "price": rec["Price"],
                    "min_qty": rec["Qty"],
                    "delay": int(rec["DaysForDelivery"]),
                }
                suppPrice = self.env["product.supplierinfo"].create(vals)
                _progress_logger(
                    iterator=idx,
                    all_records=records,
                    additional_info=suppPrice
                    and suppPrice.product_tmpl_id.default_code,
                )
        _logger.warning("<--- IMPORTAZIONE SUPPLIER PRICELIST TERMINATA --->")
