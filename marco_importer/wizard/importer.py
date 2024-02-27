from typing import Dict, List

import requests
from odoo import api, fields, models, Command
import logging

_logger = logging.getLogger(__name__)
# _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
# _logger.info('Another transaction already locked documents rows. Cannot process documents.')
BASE_URL = "https://api.marco.it/odoo/"


class MarcoImporter(models.TransientModel):
    _name = "marco.importer"

    url = fields.Char(
        string="URL",
        required=True,
        default=BASE_URL,
    )

    import_type = fields.Selection(
        selection=[("partner", "Partner"), ("bom", "BOM"), ("items", "Items")],
        string="Import Type",
        required=True,
        default="items",
    )

    @api.onchange("import_type")
    def _onchange_import_type(self):
        if self.import_type == "items":
            self.url = BASE_URL + "items"
        elif self.import_type == "bom":
            self.url = BASE_URL + "bom"
        elif self.import_type == "partner":
            self.url = BASE_URL + "partners"

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

    def import_items(self, records):
        _logger.warning("<--- IMPORTAZIONE ITEMS INIZIATA --->")
        for rec in records:
            # uom=self.env["uom.uom"].search([("name","=",rec["uom_id"])]) #deprecato -> ora uso l'id xml che è indipendente dalla lingua ed è univoco
            uom = self.env.ref(
                rec["uom_id"]
            )  # con ref cerco all'interno della tabella degli id xml
            uom_po = self.env.ref(rec["uom_po_id"])
            vals = {
                "default_code": rec["default_code"],
                "name": rec["name"],
                "barcode": rec["barcode"],
                "sale_ok": rec["sale_ok"] == "1",
                "purchase_ok": rec["purchase_ok"] == "1",
                "uom_id": uom.id,
                "uom_po_id": uom_po.id,
                "detailed_type": rec["detailed_type"],
                "standard_price": rec["standard_price"],
                "list_price": rec["basePrice"],
            }

            product_template_id = self.env["product.template"].search(
                [("default_code", "=", rec["default_code"])]
            )
            if product_template_id:
                product_template_id.write(vals)
                # _logger.warning(uom,uom_po,vals)
            else:
                product_template_id = self.env["product.template"].create(vals)
                # _logger.warning(uom,uom_po,vals)
            if rec["detailed_type"] == "product":
                product_product_id = self.env["product.product"].search(
                    [("product_tmpl_id", "=", product_template_id.id)]
                )
                warehouse = self.env["stock.warehouse"].search(
                    [("company_id", "=", self.env.company.id)], limit=1
                )
                self.env["stock.quant"].with_context(inventory_mode=True).create(
                    {
                        "product_id": product_product_id.id,
                        "location_id": warehouse.lot_stock_id.id,
                        "inventory_quantity": rec["bookInv"],
                    }
                ).action_apply_inventory()
        _logger.warning("<--- IMPORTAZIONE ITEMS TERMINATA --->")
        # _logger.warning({"quants_ids":quants_ids, "cippa":stock_inventory_conflict,"lippa":stock_inventory_conflict.quant_ids})

        # self.env.cr.commit()

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
        for rec in records:
            # cerco lo stato partendo dall'ISO Code se non esiste fermo tutto
            domain = [("code", "=", rec["ISOCountryCode"])]
            country = self.env["res.country"].search(domain)
            if not country:
                raise ValueError(f"Country {rec['ISOCountryCode']} not found")

            # cerco la provincia, usando lo stato
            if rec["County"]:
                domain = [("code", "=", rec["County"]), ("country_id", "=", country.id)]
                state = self.env["res.country.state"].search(domain)
                if not state:
                    raise ValueError(
                        f"State {rec['County']}{rec['ISOCountryCode']} not found"
                    )
            else:
                state = False

            # instanzio category come array vuoto
            category = []
            # cerco il settore nelle categorie dei partners e la creo se non esiste
            if rec["settore"]:
                domain = [("name", "=", rec["settore"])]
                settore = self.env["res.partner.category"].search(domain)
                if not settore:
                    settore = self.env["res.partner.category"].create(
                        {"name": rec["settore"]}
                    )
                category.append(settore.id)
            # cerco la tipolgia nelle categorie dei partners e la creo se non esiste
            if rec["tipologia"]:
                domain = [("name", "=", rec["tipologia"])]
                tipologia = self.env["res.partner.category"].search(domain)
                if not tipologia:
                    tipologia = self.env["res.partner.category"].create(
                        {"name": rec["tipologia"]}
                    )
                category.append(tipologia.id)

            if not category:
                category = False

            vals = {
                "name": rec["CompanyName"],
                "ref": rec["CustSupp"],
                "vat": rec["FiscalCode"],
                "street": rec["Address"],
                "zip": rec["ZIPCode"],
                "city": rec["City"],
                "phone": rec["Telephone1"],
                "website": rec["Internet"],
                # "email": rec["EMail"],
                # "CODICE FISCALE":rec["FiscalCode"]
                "is_company": rec["isCompany"],
                "vat": rec["TaxIdNumber"],
                "country_id": country.id,
                "state_id": state and state.id,
                "category_id": category and [Command.set(category)],
            }
            # __import__('pdb').set_trace()
            partner_id = self.env["res.partner"].search([("ref", "=", rec["CustSupp"])])
            if partner_id:
                partner_id.write(vals)
            else:
                partner_id = self.env["res.partner"].create(vals)

            partner_id.email = False

            _logger.warning(partner_id.name)
            # self.env.cr.commit()
