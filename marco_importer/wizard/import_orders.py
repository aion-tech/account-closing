from odoo import api, fields, models, Command
from .progress_logger import _progress_logger, _logger
from datetime import datetime

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    orders = fields.Boolean()

    def import_orders(self, records):
        _logger.warning("<--- IMPORTAZIONE ORDERS HEAD INIZIATA --->")
        
        # Creazione di un recordset vuoto per raccogliere gli ordini da confermare
        order_head_ids = self.env["sale.order"].browse([])

        for idx, rec in enumerate(records):
            customer_id = self.env["res.partner"].search(
                [("ref", "=", rec["Customer"])]
            )
            if not customer_id:
                print(rec["Customer"], customer_id)
                continue

            vals = {
                "origin": rec["InternalOrdNo"],
                "commitment_date": datetime.strptime(
                    str(rec["ConfirmedDeliveryDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "date_order": datetime.strptime(
                    str(rec["OrderDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "partner_id": customer_id.id,
                "client_order_ref": rec.get("YourReference"),
                "picking_policy": "one",
            }
            order_head_id = self.env["sale.order"].search(
                [("origin", "=", rec["InternalOrdNo"])], limit=1
            )
            if order_head_id:
                order_head_id.write(vals)
            else:
                order_head_id = self.env["sale.order"].create(vals)

            # Aggiunge l'ordine al recordset per conferma successiva
            order_head_ids |= order_head_id

            # Itera sulle linee all'interno di ogni testata
            for line_idx, line_rec in enumerate(rec["lines"]):
                # Gestione delle note
                
                if not line_rec.get("Item"):
                    description = line_rec["Description"] if line_rec["Description"].strip() else " "
                    note_vals = {
                        "order_id": order_head_id.id,
                        "name": description,
                        "sequence": line_rec["Line"],
                        "display_type": "line_note",
                        "product_uom_qty": 0.0,
                        "price_unit": 0.0,
                    }
                    
                    # Cerca e aggiorna la nota o crea una nuova nota se non esiste
                    note_line_id = self.env["sale.order.line"].search(
                        [
                            ("order_id", "=", order_head_id.id),
                            ("sequence", "=", line_rec["Line"]),
                            ("display_type", "=", "line_note"),
                        ]
                    )
                    if note_line_id:
                        note_line_id.write(note_vals)
                    else:
                        self.env["sale.order.line"].create(note_vals)
                    continue  # Salta al prossimo ciclo per le note

                # Gestione delle linee con prodotto
                product_template_id = self.env["product.product"].search(
                    [("default_code", "=", line_rec["Item"])]
                )
                if not product_template_id or order_head_id.origin != line_rec["InternalOrdNo"]:
                    continue

                line_vals = {
                    "order_id": order_head_id.id,
                    "product_id": product_template_id.id,
                    "name": product_template_id.name,
                    "product_uom_qty": float(line_rec["Qty"]),
                    "price_unit": float(line_rec["UnitValue"]),
                    "sequence": line_rec["Line"],
                    "customer_lead": 0.0,
                    "discount":float(line_rec["Discount1"]),
                    "discount2":float(line_rec["Discount2"]),
                }
                
                order_line_id = self.env["sale.order.line"].search(
                    [
                        ("order_id", "=", order_head_id.id),
                        ("product_id", "=", product_template_id.id),
                        ("sequence", "=", line_rec["Line"]),
                    ]
                )
                
                if order_line_id:
                    order_line_id.write(line_vals)
                else:
                    order_line_id = self.env["sale.order.line"].create(line_vals)

            # Log dei progressi per ogni ordine
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=f'{order_head_id.origin} - rows = {len(rec["lines"])}',
            )

        # Conferma tutti gli ordini insieme alla fine
        order_head_ids.filtered(lambda o: o.state == 'draft').action_confirm()

        _logger.warning("<--- IMPORTAZIONE ORDERS HEAD TERMINATA --->")
