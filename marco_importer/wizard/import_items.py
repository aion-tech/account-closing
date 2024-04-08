from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    items = fields.Boolean(string="Items")
    
    def import_items(self, records):
        _logger.warning("<--- IMPORTAZIONE ITEMS INIZIATA --->")
        for idx, rec in enumerate(records):
            # Definisco quali rotte può avere l'articolo
            route_ids = False
            if rec["outsourced"] == "0" and (rec["magoNature"] == "Semilavorato" or rec["magoNature"] == "Finito" ):
                manufacture = self.env.ref("mrp.route_warehouse0_manufacture")
                route_ids = [Command.set([manufacture.id])]
            else:
                buy = self.env.ref("purchase_stock.route_warehouse0_buy")
                route_ids = [Command.set([buy.id])]
            # con ref cerco all'interno della tabella degli id xml
            uom = self.env.ref(rec["uom_id"])
            uom_po = self.env.ref(rec["uom_po_id"])

            # inizializzo le variabili delle categorie a False
            category = self.env.ref("product.product_category_all")
            catDesc = False
            subCatDesc = False
            product_tag = False

            # cerco il categoria nelle categorie dei prodotti e la creo se non esiste
            if not rec["categoryDescription"] == "" and rec["categoryDescription"]:
                domain = [
                    ("name", "=", rec["categoryDescription"]),
                    ("parent_id", "=", False),
                ]
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
                domain = [
                    ("name", "=", rec["subCategoryDescription"]),
                    ("parent_id", "=", catDesc and catDesc.id),
                ]
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
                domain = [
                    ("name", "=", rec["product_tag"]),
                ]
                product_tag = self.env["product.tag"].search(domain)
                if not product_tag:
                    product_tag = self.env["product.tag"].create(
                        {
                            "name": rec["product_tag"],
                        }
                    )

                domain = [
                    ("name", "=", rec["product_tag"]),
                    ("parent_id", "=", subCatDesc and subCatDesc.id),
                ]
                subSubCatDesc = self.env["product.category"].search(domain)
                if not subSubCatDesc:
                    subSubCatDesc = self.env["product.category"].create(
                        {
                            "name": rec["product_tag"],
                            "parent_id": subCatDesc and subCatDesc.id,
                        }
                    )
                category = subSubCatDesc

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
                "product_tag_ids": product_tag and [Command.set([product_tag.id])],
                "categ_id": category.id,
            }

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
                        "inventory_quantity": rec["bookInv"] if rec["bookInv"] and rec["bookInv"] > 0 else 0,# ignoro tutti i negativi e imposto a 0 la quantità
                    }
                ).action_apply_inventory()

            #gestione aree per mrp multilever
            product_id=self.env["product.product"].search(
                [("default_code", "=", rec["default_code"])]
            )

            product_mrp_area=self.env["product.mrp.area"].search(
                [("product_id", "=", product_id.id)]
            )
            vals={
                "mrp_area_id":self.env.ref("mrp_multi_level.mrp_area_stock_wh0").id,
                "product_id":product_id.id,
                "location_proc_id":self.env.ref("stock.stock_location_stock").id,
                "mrp_nbr_days":14,
                #finchè proviamo l'mrp questo lo lasciamo commentato perchè se no crea ordini di produzione per ripristinare le scorte di sicurezza
                #"mrp_minimum_stock":rec["minimumStock"],
                #"mrp_qty_multiple":rec["reorderingLotSize"]
            }
            if product_mrp_area:
                product_mrp_area.write(vals)
            else:            
                product_mrp_area = self.env["product.mrp.area"].create(vals)
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=product_template_id.default_code,
            )
        _logger.warning("<--- IMPORTAZIONE ITEMS TERMINATA --->")