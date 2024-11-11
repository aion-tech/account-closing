from odoo import models, fields, api

class StockDeliveryNote(models.Model):
    _inherit = 'stock.delivery.note'

    def action_invoice(self, invoice_method=False):
        res = super().action_invoice(invoice_method=invoice_method)
        for delivery_note in self:
            # finding fiscal document type created from ddt
            fiscal_doc_type_created_from_ddt = self.env['fiscal.document.type'].search([
                ('created_from_ddt', '=', True)
            ], limit=1)
            if fiscal_doc_type_created_from_ddt:
                for delivery_note_invoice in delivery_note.invoice_ids:
                    delivery_note_invoice.fiscal_document_type_id = fiscal_doc_type_created_from_ddt.id
        return res