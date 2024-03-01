from typing import Dict, List

import requests
from odoo import api, fields, models, Command
import logging

_logger = logging.getLogger(__name__)
# _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
# _logger.info('Another transaction already locked documents rows. Cannot process documents.')
BASE_URL = "https://api.marco.it/odoo/"


def _progress_logger(iterator: int, all_records: list, additional_info: str = ""):
    _logger.warning(
        f"<--- {str(iterator+1)} | {str(len(all_records))} ---> {additional_info}"
    )


class MarcoImporter(models.TransientModel):
    _name = "marco.importer"

    url = fields.Char(
        string="URL",
        required=True,
        default=BASE_URL,
    )

    import_type = fields.Selection(
        selection=[
            ("partner", "Partner"),
            ("bomComponent", "BOM COMPONENT"),
            ("bomHead", "BOM HEAD"),
            ("items", "Items"),
        ],
        string="Import Type",
        required=True,
        default="bomHead",
    )

    @api.onchange("import_type")
    def _onchange_import_type(self):
        if self.import_type == "items":
            self.url = BASE_URL + "items"
        elif self.import_type == "bomComponent":
            self.url = BASE_URL + "bom/component"
        elif self.import_type == "bomHead":
            self.url = BASE_URL + "bom/head"
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

        if self.import_type == "bomHead":
            self.import_bom_heads(records)

        if self.import_type == "bomComponent":
            self.import_bom_components(records)

    def import_items(self, records):
        _logger.warning("<--- IMPORTAZIONE ITEMS INIZIATA --->")
        for idx, rec in enumerate(records):
            # con ref cerco all'interno della tabella degli id xml
            uom = self.env.ref(rec["uom_id"])
            uom_po = self.env.ref(rec["uom_po_id"])

            # inizializzo le variabili delle categorie a False
            category = False
            catDesc = False
            subCatDesc = False
            tag = False

            # cerco il categoria nelle categorie dei prodotti e la creo se non esiste
            if not rec["categoryDescription"] == "" and rec["categoryDescription"]:
                domain = [("name", "=", rec["categoryDescription"])]
                catDesc = self.env["product.category"].search(domain)
                if not catDesc:
                    catDesc = self.env["product.category"].create(
                        {"name": rec["categoryDescription"]}
                    )
                category = catDesc
            # cerco la sotto categoria nelle categorie dei prodotti e la creo se non esiste legandola ad una categoria
            if (
                not rec["subCategoryDescription"] == ""
                and rec["subCategoryDescription"]
            ):
                domain = [("name", "=", rec["subCategoryDescription"])]
                subCatDesc = self.env["product.category"].search(domain)
                if not subCatDesc:
                    subCatDesc = self.env["product.category"].create(
                        {
                            "name": rec["subCategoryDescription"],
                            "parent_id": catDesc and catDesc.id,
                        }
                    )
                category = subCatDesc
            # cerco il tipo nella categoria dei prodotti e la creo se non esiste legandola ad una sottocategoria
            if not rec["product_tag"] == "" and rec["product_tag"]:
                domain = [("name", "=", rec["product_tag"])]
                tag = self.env["product.category"].search(domain)
                if not tag:
                    tag = self.env["product.category"].create(
                        {
                            "name": rec["product_tag"],
                            "parent_id": subCatDesc and subCatDesc.id,
                        }
                    )
                category = tag

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
            if category:
                vals["categ_id"] = category.id

            product_template_id = self.env["product.template"].search(
                [("default_code", "=", rec["default_code"])]
            )
            if product_template_id:
                product_template_id.write(vals)
            else:
                product_template_id = self.env["product.template"].create(vals)

            # gestione della giacenza di magazzino
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

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=product_template_id.default_code,
            )
        _logger.warning("<--- IMPORTAZIONE ITEMS TERMINATA --->")

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
                    if bom:
                        bom.write(
                            {
                                "type": "subcontract",
                                "subcontractor_ids": partner_id
                                and [Command.set([partner_id.id])],
                            }
                        )
                    else:
                        bom = self.env["mrp.bom"].create(
                            {
                                "product_tmpl_id": product.id,
                                "type": "subcontract",
                                "subcontractor_ids": partner_id
                                and [Command.set([partner_id.id])],
                            }
                        )
                else:
                    if bom:
                        bom.write(
                            {
                                "type": rec["type"],
                            }
                        )
                    else:
                        bom = self.env["mrp.bom"].create(
                            {
                                "product_tmpl_id": product.id,
                                "type": rec["type"],
                            }
                        )
            _progress_logger(
                iterator=idx, all_records=records, additional_info=bom and product.name
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")

    def import_bom_components(self, records):
        for idx, rec in enumerate(records):
            bom_product = self.env["product.template"].search(
                [("default_code", "=", rec["bom"])]
            )
            bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", bom_product.id)])

            component_product = self.env["product.product"].search(
                [("default_code", "=", rec["component"])]
            )

            if bom_product and component_product:
                bom_line = self.env["mrp.bom.line"].search(
                    [("product_id", "=", component_product.id)]
                )
                if bom_line:
                    bom_line.write(
                        {
                            "product_qty": rec["qty"],
                        }
                    )
                else:
                    bom_line = self.env["mrp.bom.line"].create(
                        {
                            "bom_id": bom.id,
                            "product_id": component_product.id,
                            "product_qty": rec["qty"],
                        }
                    )

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=component_product and component_product.name,
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")

    def import_partner_data(self, records):
        _logger.warning("<--- IMPORTAZIONE PARTNERS INIZIATA --->")
        for idx, rec in enumerate(records):
            # cerco lo stato partendo dall'ISO Code se non esiste fermo tutto
            if rec["Country"]:
                domain = [("code", "=", rec["Country"])]
                country = self.env["res.country"].search(domain)
                if not country:
                    raise ValueError(f"Country {rec['Country']} not found:{rec}")

                # cerco la provincia, usando lo stato
                if rec["County"]:
                    domain = [
                        ("code", "=", rec["County"]),
                        ("country_id", "=", country.id),
                    ]
                    state = self.env["res.country.state"].search(domain)
                    if not state:
                        raise ValueError(
                            f"State {rec['County']} - {rec['Country']} not found:{rec}"
                        )
                else:
                    state = False
            else:
                country = False
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
                "vat": rec["TaxIdNumber"],
                # "fiscalcode":rec["FiscalCode"],
                "street": rec["Address"],
                "zip": rec["ZIPCode"],
                "city": rec["City"],
                "phone": rec["Telephone1"],
                "website": rec["Internet"],
                # "email": rec["EMail"],
                "is_company": rec["isCompany"],
                "vat": rec["TaxIdNumber"],
                "country_id": country and country.id,
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

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=partner_id and partner_id.name,
            )
        _logger.warning("<--- IMPORTAZIONE PARTNERS TERMINATA --->")
        # self.env.cr.commit()
