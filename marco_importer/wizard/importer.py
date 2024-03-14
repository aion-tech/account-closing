from typing import Dict, List

import requests
from odoo import api, fields, models, Command
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)
# _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
# _logger.info('Another transaction already locked documents rows. Cannot process documents.')

# __import__('pdb').set_trace() # SETTA UN PUNTO DI DEBUG

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
            ("partner", "PARTNERS"),
            ("items", "ITEMS"),
            ("bomHead", "BOM HEAD"),
            ("bomComponent", "BOM COMPONENT"),
            ("workcenter", "WORKCENTERS"),
            ("bomOperation", "BOM OPERATIONS"),
            ("supplierPricelist", "SUPPLIER PRICELIST"),
            ("debug", "--DEBUG--"),
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
        elif self.import_type == "workcenter":
            self.url = BASE_URL + "bom/workcenter"
        elif self.import_type == "bomOperation":
            self.url = BASE_URL + "bom/operation"
        elif self.import_type == "supplierPricelist":
            self.url = BASE_URL + "supplier/pricelist"

    def _check_url(self):
        return self.url.startswith("https")

    def import_all_data(self):
        _logger.warning("<--- INIZIO IMPORTAZIONE DI TUTTO --->")
        self.url = BASE_URL + "partners"
        res = requests.get(self.url)
        records = res.json()
        self.import_partner_data(records)

        self.url = BASE_URL + "items"
        res = requests.get(self.url)
        records = res.json()
        self.import_items(records)

        self.url = BASE_URL + "bom/head"
        res = requests.get(self.url)
        records = res.json()
        self.import_bom_heads(records)

        self.url = BASE_URL + "bom/component"
        res = requests.get(self.url)
        records = res.json()
        self.import_bom_components(records)

        self.url = BASE_URL + "bom/workcenter"
        res = requests.get(self.url)
        records = res.json()
        self.import_workcenters(records)

        self.url = BASE_URL + "bom/operation"
        res = requests.get(self.url)
        records = res.json()
        self.import_bom_operations(records)

        self.url = BASE_URL + "supplier/pricelist"
        res = requests.get(self.url)
        records = res.json()
        self.import_supplier_pricelist(records)

        _logger.warning("<--- IMPORTAZIONE COMPLETATA --->")

    def import_data(self):
        if not self._check_url():
            raise ValueError("URL must start with 'https'")

        res = requests.get(self.url)
        records = res.json()
        if self.import_type == "items":
            self.import_items(records)

        elif self.import_type == "partner":
            self.import_partner_data(records)

        elif self.import_type == "bomHead":
            self.import_bom_heads(records)

        elif self.import_type == "bomComponent":
            self.import_bom_components(records)

        elif self.import_type == "workcenter":
            self.import_workcenters(records)

        elif self.import_type == "bomOperation":
            self.import_bom_operations(records)

        elif self.import_type == "supplierPricelist":
            self.import_supplier_pricelist(records)

        elif self.import_type == "debug":
            self.debug()

    def debug(self):
        res = self.env["stock.route"].search([])
        for route in res:
            print(route.name, route.id)
        print(res)
        __import__("pdb").set_trace()

    def import_items(self, records):
        _logger.warning("<--- IMPORTAZIONE ITEMS INIZIATA --->")
        for idx, rec in enumerate(records):
            # Definisco quali rotte può avere l'articolo
            route_ids = False
            if rec["outsourced"] == "0" and rec["magoNature"] == "Semilavorato":
                manufacture = self.env["stock.route"].search([("id", "=", 6)])
                route_ids = [Command.set([manufacture.id])]
            else:
                buy = self.env["stock.route"].search([("id", "=", 5)])
                route_ids = [Command.set([buy.id])]

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
                "route_ids": route_ids,
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

    def import_supplier_pricelist(self, records):
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

    def import_bom_components(self, records):
        for idx, rec in enumerate(records):
            bom_product = self.env["product.template"].search(
                [("default_code", "=", rec["bom"])]
            )
            bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", bom_product.id)])

            component_product = self.env["product.product"].search(
                [("default_code", "=", rec["component"])]
            )
            # __import__("pdb").set_trace()
            # Se la bom padre è di natura subcontract devo aggiungere alle rotte del figlio la rotta 8 (Resupply Subcontractor on Order)
            if bom.type == "subcontract":
                resupply_subcontractor_on_order = self.env["stock.route"].search(
                    [("id", "=", 8)]
                )
                component_product.route_ids = [
                    Command.link(resupply_subcontractor_on_order.id)
                ]

            if bom_product and component_product and bom:
                bom_line = self.env["mrp.bom.line"].search(
                    [("product_id", "=", component_product.id)]
                )
                vals = {
                    "bom_id": bom.id,
                    "product_id": component_product.id,
                    "product_qty": rec["qty"],
                }
                if bom_line:
                    bom_line.write(vals)
                else:
                    bom_line = self.env["mrp.bom.line"].create(vals)

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=component_product and component_product.name,
            )
        _logger.warning("<--- IMPORTAZIONE BOM HEAD TERMINATA --->")

    def import_bom_operations(self, records):
        _logger.warning("<--- IMPORTAZIONE OPERAZIONI INIZIATA --->")
        for idx, rec in enumerate(records):
            product_id = self.env["product.template"].search(
                [("default_code", "=", rec["bom"])]
            )
            if not product_id:
                continue

            bom_id = self.env["mrp.bom"].search(
                [("product_tmpl_id", "=", product_id.id)]
            )
            if not bom_id or bom_id.type == "subcontract":
                continue

            workcenter_id = self.env["mrp.workcenter"].search(
                [("code", "=", rec["wc_code"])]
            )

            if not workcenter_id:
                raise ValueError(f"WORKCENTER {rec['wc_code']} not found:{rec}")

            vals = {
                "name": rec["OperationDesc"],
                "bom_id": bom_id.id,
                "workcenter_id": workcenter_id.id,
                "time_mode": "manual",
                "time_cycle_manual": rec["time_cycle_manual"],
                "sequence": rec["RtgStep"],
                "note": rec["note"],
            }
            operation_id = self.env["mrp.routing.workcenter"].search(
                [
                    ("name", "=", rec["OperationDesc"]),
                    ("bom_id", "=", bom_id.id),
                    ("workcenter_id", "=", workcenter_id.id),
                ]
            )
            if operation_id:
                operation_id.write(vals)
            else:
                operation_id = self.env["mrp.routing.workcenter"].create(vals)

            _progress_logger(
                iterator=idx, all_records=records, additional_info=operation_id.name
            )
        _logger.warning("<--- IMPORTAZIONE OPERAZIONI TERMINATA --->")

    def import_workcenters(self, records):
        _logger.warning("<--- IMPORTAZIONE WORKCENTERS INIZIATA --->")
        for idx, rec in enumerate(records):
            if rec["Outsourced"] == "1":
                continue
            vals = {
                "name": rec["name"],
                "code": rec["code"],
                "costs_hour": rec["costs_hour"],
                "note": rec["note"],
            }
            workcenter_id = self.env["mrp.workcenter"].search(
                [("code", "=", rec["code"])]
            )
            if workcenter_id:
                workcenter_id.write(vals)
            else:
                workcenter_id = self.env["mrp.workcenter"].create(vals)
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=workcenter_id and workcenter_id.code,
            )
        _logger.warning("<--- IMPORTAZIONE WORKCENTERS TERMINATA --->")

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

            partner_id = self.env["res.partner"].search([("ref", "=", rec["CustSupp"])])
            if partner_id:

                partner_id.with_context(no_vat_validation=True).write(
                    vals
                )  # per ora ignoro tutti i check sul VAT no
            else:
                partner_id = (
                    self.env["res.partner"]
                    .with_context(no_vat_validation=True)
                    .create(vals)
                )  # per ora ignoro tutti i check sul VAT no

            partner_id.email = False

            vat_error_message = "P.IVA ERRATA"
            vat_checker = (vat_error_message, False)[
                partner_id.simple_vat_check(
                    country_code=rec["ISOCountryCode"],
                    vat_number=rec["TaxIdNumber"],
                )
            ]
            if vat_checker and rec["TaxIdNumber"] != "":
                vat_checker_tag = self.env["res.partner.category"].search(
                    [("name", "=", vat_checker)]
                )
                if not vat_checker_tag:
                    vat_checker_tag = self.env["res.partner.category"].create(
                        {"name": vat_checker}
                    )

                partner_id.category_id = [Command.link(vat_checker_tag.id)]

            else:
                vat_was_wrong = partner_id.category_id.search(
                    [("name", "=", vat_error_message)]
                )
                if vat_error_message:
                    command = Command.unlink(vat_was_wrong.id)

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=vat_checker,  # partner_id and partner_id.name,
            )

        _logger.warning("<--- IMPORTAZIONE PARTNERS TERMINATA --->")
        # self.env.cr.commit()
