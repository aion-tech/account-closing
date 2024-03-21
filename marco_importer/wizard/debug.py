from odoo import api, fields, models, Command

from . import static_data


BASE_URL=static_data.BASE_URL
import_method_map=static_data.import_method_map

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

   

    def debug(self):
        bom_product = self.env["product.template"].search(
            [("default_code", "=", "S5010006")]
        )
        bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", bom_product.id)])

        bom_line = self.env["mrp.bom.line"].search([("bom_id", "=", bom.id)])
        __import__("pdb").set_trace()

        """
        res = self.env["res.config.settings"].new({"group_uom": True}).execute()

        # con new lo lasci in memoria, con create invece lo crei nel database e viene pulito una volta al giorno  dal crono "auto vacuum ..."
        # __import__("pdb").set_trace()
        res = self.env["stock.route"].search([])
        for route in res:
            print(route.name, route.id)
        print(res)
        # __import__("pdb").set_trace()
        """
