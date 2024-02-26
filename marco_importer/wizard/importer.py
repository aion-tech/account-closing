from typing import Dict, List

import requests
from odoo import api, fields, models



class MarcoImporter(models.TransientModel):
    _name = "marco.importer"

    url = fields.Char(
        string="URL",
        required=True,
        default="https://api.marco.it/odoo/items",
    )
    import_type = fields.Selection(
        selection=[("partner", "Partner"), ("bom", "BOM"),("items","Items")],
        string="Import Type",
        required=True,
        default="items",
    )

    def _check_url(self):
        return self.url.startswith("https")

    def import_data(self):
        if not self._check_url():
            raise ValueError("URL must start with 'https'")

        res = requests.get(self.url)
        records = res.json()
        if self.import_type == "items":
            self.import_items(records)

        if self.import_type == "partner":
            self.import_partner_data(records)

        if self.import_type == "bom":
            self.import_bom_data(records)

    def import_items(self,records):
        for rec in records:
            #uom=self.env["uom.uom"].search([("name","=",rec["uom_id"])]) #deprecato -> ora uso l'id xml che è indipendente dalla lingua ed è univoco
            uom=self.env.ref(rec["uom_id"]) #con ref cerco all'interno della tabella degli id xml
            uom_po=self.env.ref(rec["uom_po_id"])
            vals = {
                "default_code": rec["default_code"],
                "name": rec["name"],
                "barcode": rec["barcode"],
                "sale_ok": rec["sale_ok"]=="1",
                "purchase_ok": rec["purchase_ok"]=="1",
                "uom_id": uom.id,
                "uom_po_id": uom_po.id,
                "detailed_type": rec["detailed_type"],
                "standard_price": rec["standard_price"],
                "list_price":rec["basePrice"]
            }
            
           
            product_template_id = self.env["product.template"].search(
                [("default_code", "=", rec["default_code"])]

            )
            if product_template_id:
                product_template_id.write(vals)
                #print(uom,uom_po,vals)
            else:
                product_template_id = self.env["product.template"].create(vals)
                #print(uom,uom_po,vals)
            if rec["detailed_type"] =="product":
                product_product_id=self.env["product.product"].search([("product_tmpl_id","=",product_template_id.id)])
            
                update_qty_wizard=self.env["stock.change.product.qty"].new({"product_tmpl_id":product_template_id.id,"product_id":product_product_id.id,"new_quantity":rec["bookInv"]})
                update_qty_wizard.change_product_qty()
            
            #stock_quant_id=self.env["stock.quant"].search([("quantity",">=",0),("product_id","=",product_product_id.id)])
            """  if stock_quant_id:
                stock_quant_id.action_apply_inventory()
                """
                
            #apply_on_all_wizard=self.env["stock.inventory.adjustment.name"]
        """ quants_ids=self.env["stock.quant"].search([])
        quants_outdated=quants_ids.filtered(lambda quant: quant.is_outdated)
        print(quants_outdated)
        for q in quants_outdated:
            print(q.is_outdated,q.inventory_diff_quantity,q.inventory_quantity,q.quantity)
        stock_inventory_conflict=self.env["stock.inventory.conflict"].new({"quant_ids":quants_ids,"quant_to_fix_ids":quants_outdated})
        stock_inventory_conflict.action_keep_difference() """
        print("import terminato")
        #print({"quants_ids":quants_ids, "cippa":stock_inventory_conflict,"lippa":stock_inventory_conflict.quant_ids})
              
            #self.env.cr.commit()
       

    def import_bom_data(self, records):
        # product = self.env["product.template"].create(
        #     {
        #         "name": "Prodotto Finito",
        #         "detailed_type": "product",
        #     }
        # )
        product = self.env["product.template"].search(
            [("default_code", "=", "PROD0001")]
        )
        if product:
            bom = self.env["mrp.bom"].create(
                {
                    "product_tmpl_id": product.id,
                    "code": "asdfasdf",
                }
            )
            bom_line = self.env["mrp.bom.line"].create({"bom_id": bom.id})

    def import_partner_data(self, records):
        for rec in records[:50]:
            vals = {
                "name": rec["CompanyName"],
                "ref": rec["CustSupp"],
                "vat": rec["FiscalCode"],
                "street": rec["Address"],
                "zip": rec["ZIPCode"],
                "city": rec["City"],
                "phone": rec["Telephone1"],
                "website": rec["Internet"],
                "email": rec["EMail"],
                "is_company": rec["isCompany"],
            }
            domain = [("code", "=", rec["ISOCountryCode"])]
            country = self.env["res.country"].search(domain)

            if not country:
                raise ValueError(f"Country {rec['ISOCountryCode']} not found")

            vals["country_id"] = country.id

            existing_partner = self.env["res.partner"].search(
                [("ref", "=", rec["CustSupp"])]
            )
            if existing_partner:
                existing_partner.write(vals)
            else:
                existing_partner = self.env["res.partner"].create(vals)

            existing_partner.email = False

            print(existing_partner.name)
            #self.env.cr.commit()
