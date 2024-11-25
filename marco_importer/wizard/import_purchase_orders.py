from odoo import api, fields, models, Command
from .progress_logger import _progress_logger, _logger
from datetime import datetime


class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    purchase_orders = fields.Boolean()
    purchase_orders_include_delivered = fields.Boolean()

    def import_purchase_orders(self, records, include_delivered=True):
        """
        Importa gli ordini di acquisto.
        Elimina gli ordini esistenti senza picking prima di importare nuovi dati.
        """
        # Trova tutti gli ordini di acquisto senza picking
        purchase_orders_no_pickings = self.env["purchase.order"].search(
            [("picking_ids", "=", False), ("origin", "!=", False)]
        )

        if purchase_orders_no_pickings:
            _logger.info(
                f"Eliminazione di {len(purchase_orders_no_pickings)} ordini di acquisto senza picking."
            )
            # Annulla gli ordini
            purchase_orders_no_pickings.button_cancel()
            # Elimina gli ordini
            purchase_orders_no_pickings.unlink()

        _logger.warning("<--- IMPORTAZIONE ORDERS HEAD INIZIATA --->")

        order_head_ids_to_confirm = self.env[
            "purchase.order"
        ]  # Recordset per gli ordini da confermare
        order_head_ids_to_reserve = self.env[
            "purchase.order"
        ]  # Recordset per gli ordini da confermare e riservare

        # Ordina le testate per InternalOrdNo crescente
        records = sorted(records, key=lambda x: x["InternalOrdNo"])

        for idx, rec in enumerate(records):
            supplier_id = self.env["res.partner"].search(
                [("ref", "=", rec["Supplier"])]
            )
            if not supplier_id:
                print(rec["Supplier"], supplier_id)
                continue
            if not include_delivered and rec.get("Delivered") == "1":
                _logger.warning(
                    f"L'ordine {rec['InternalOrdNo']} è stato già consegnato. Riga ignorata."
                )
                continue

            # Imposta la valuta in base al campo `Currency` se disponibile, altrimenti usa "EUR"
            currency_code = rec.get("Currency", "EUR")
            currency = self.env.ref(f"base.{currency_code}", raise_if_not_found=False)
            if not currency:
                _logger.warning(
                    f"Valuta {currency_code} non trovata, uso 'EUR' come fallback."
                )
                currency = self.env.ref("base.EUR", raise_if_not_found=False)
            if not currency:
                raise ValueError(
                    "La valuta predefinita 'EUR' non è configurata nel sistema."
                )

            payment_term_ref = rec["payment_term"] and rec["payment_term"].strip()
            payment_term = payment_term_ref and self.env.ref(
                f"l10n_it_marco_extra.{payment_term_ref}"
            )
            vals = {
                "origin": rec["InternalOrdNo"],
                "date_planned": datetime.strptime(
                    str(rec["ConfirmedDeliveryDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "date_order": datetime.strptime(
                    str(rec["OrderDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "partner_id": supplier_id.id,
                "currency_id": currency and currency.id,
                "payment_term_id": payment_term and payment_term.id,
            }

            order_head_id = self.env["purchase.order"].search(
                [("origin", "=", rec["InternalOrdNo"])], limit=1
            )
            if order_head_id:
                order_head_id.write(vals)
            else:
                order_head_id = self.env["purchase.order"].create(vals)

            # Aggiunge l'ordine al recordset appropriato per conferma e riserva/validazione
            if rec.get("Delivered") == "1":
                order_head_ids_to_reserve |= order_head_id
            else:
                order_head_ids_to_confirm |= order_head_id

            for line_idx, line_rec in enumerate(rec["lines"]):
                product_template_id = self.env["product.product"].search(
                    [("default_code", "=", line_rec["Item"])]
                )

                # Gestione delle note
                if not product_template_id:
                    if order_head_id.origin == line_rec["InternalOrdNo"]:
                        description = (
                            line_rec["Description"]
                            if line_rec["Description"].strip()
                            else " "
                        )
                        vals = {
                            "order_id": order_head_id.id,
                            "name": description,
                            "sequence": line_rec["Line"],
                            "display_type": "line_note",
                            "product_qty": 0.0,
                        }

                        order_line_id = self.env["purchase.order.line"].search(
                            [
                                ("order_id", "=", order_head_id.id),
                                ("sequence", "=", line_rec["Line"]),
                                ("display_type", "=", "line_note"),
                            ]
                        )
                        if order_line_id:
                            order_line_id.write(vals)
                        else:
                            order_line_id = self.env["purchase.order.line"].create(vals)

                    continue  # Salta al prossimo ciclo se è una nota

                # Gestione delle linee con prodotto
                if order_head_id.origin != line_rec["InternalOrdNo"]:
                    continue
                if float(line_rec["Qty"]) <= 0:
                    _logger.warning(
                        f"La quantità per la linea {line_rec['Line']} nell'ordine {rec['InternalOrdNo']} è 0. Questa linea sarà ignorata."
                    )
                    continue  # Salta questa linea

                # Determina la quantità in base a `include_delivered`
                if not include_delivered and line_rec.get("Delivered") == "1":
                    _logger.warning(
                        f"La quantità consegnata per la linea {line_rec['Line']} è maggiore o uguale alla quantità ordinata. Questa linea sarà ignorata."
                    )
                    continue  # Salta questa linea
                else:
                    if line_rec["DeliveredQty"] == 0:
                        product_qty = float(line_rec["Qty"])
                    elif line_rec["DeliveredQty"] < line_rec["Qty"]:
                        product_qty = float(line_rec["Qty"] - line_rec["DeliveredQty"])
                    else:
                        product_qty = float(line_rec["Qty"])

                vals = {
                    "order_id": order_head_id.id,
                    "product_id": product_template_id.id,
                    "name": product_template_id.name,
                    "product_qty": product_qty,
                    "price_unit": float(line_rec["UnitValue"]),
                    "sequence": line_rec["Line"],
                    "date_planned": datetime.strptime(
                        str(line_rec["ConfirmedDeliveryDate"]), "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                }

                order_line_id = self.env["purchase.order.line"].search(
                    [
                        ("order_id", "=", order_head_id.id),
                        ("product_id", "=", product_template_id.id),
                        ("sequence", "=", line_rec["Line"]),
                    ]
                )

                if order_line_id:
                    # Confronta i valori attuali con quelli desiderati
                    update_vals = {
                        key: value
                        for key, value in vals.items()
                        if (
                            (
                                order_line_id[key].id
                                if isinstance(order_line_id[key], models.BaseModel)
                                else order_line_id[key]
                            )
                            != value
                        )
                    }

                    # Esegui il write solo se ci sono differenze
                    if update_vals:
                        order_line_id.write(update_vals)
                else:
                    order_line_id = self.env["purchase.order.line"].create(vals)

                _progress_logger(
                    iterator=idx,
                    all_records=rec["lines"],
                    additional_info=order_line_id and order_line_id.name,
                )

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=order_head_id and order_head_id.origin,
            )

        # Conferma solo gli ordini in stato "draft"
        order_head_ids_to_confirm.filtered(
            lambda o: o.state == "draft"
        ).button_confirm()

        # Conferma e gestisci il picking solo sugli ordini in stato "draft" per la conferma e "purchase" per la riserva e validazione
        order_head_ids_to_reserve.filtered(
            lambda o: o.state == "draft"
        ).button_confirm()
        """ confirmed_orders = order_head_ids_to_reserve.filtered(lambda o: o.state == 'purchase')
        confirmed_orders.picking_ids.action_set_quantities_to_reservation()
        confirmed_orders.picking_ids.button_validate()
        """
        _logger.warning("<--- IMPORTAZIONE ORDERS HEAD TERMINATA --->")
