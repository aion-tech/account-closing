from odoo import  fields, models
from .progress_logger import _progress_logger, _logger


class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    items_attributes_category = fields.Boolean()

    

    def import_items_attributes_category(self, records):
        _logger.warning("<--- IMPORTAZIONE BOM HEADS INIZIATA --->")

        for idx, rec in enumerate(records):
            category = self.env["product.attribute.category"].search(
                [("name", "=", rec["Descrizione"])]
            )
            
            if not category:
                category = self.env["product.attribute.category"].create({"name":rec["Descrizione"]})

            _progress_logger(
                iterator=idx, all_records=records, additional_info=category and category.name
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")
