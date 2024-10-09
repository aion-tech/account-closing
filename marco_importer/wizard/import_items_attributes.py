from odoo import  fields, models
from .progress_logger import _progress_logger, _logger


class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    items_attributes_category = fields.Boolean()

    

    def import_items_attributes(self, records):
        _logger.warning("<--- IMPORTAZIONE BOM HEADS INIZIATA --->")

        for idx, rec in enumerate(records):
            attribute = self.env["product.attribute"].search(
                [("name", "=", rec["Descrizione_In_Lingua_ENG"])]
            )
            category_id = self.env["product.attribute.category"].search(
                [("name", "=", rec["SetAttributi"])]
            )
            vals={
                "name":rec["Descrizione_In_Lingua_ENG"],
                "category_id":category_id.id,
                "create_variant":"dynamic",
                "display_type":"radio_circle"
            }
            if not attribute:
                category = self.env["product.attribute"].create({"name":rec["Descrizione"]})

            _progress_logger(
                iterator=idx, all_records=records, additional_info=category and category.name
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")
