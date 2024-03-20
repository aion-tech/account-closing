from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _create_document(self, vals):
        res = super()._create_document(vals)
        if vals.get("res_model") == "maintenance.request":
            request_id = self.env["maintenance.request"].browse(vals.get("res_id"))
            if request_id:
                request_id.websocket_refresh()
        return res

    def unlink(self):
        maintenance_request_attachments = self.filtered(
            lambda att: att.res_model == "maintenance.request"
        )
        request_ids = maintenance_request_attachments and self.env[
            "maintenance.request"
        ].browse(maintenance_request_attachments.mapped("res_id"))
        res = super().unlink()
        if request_ids:
            request_ids.websocket_refresh()
        return res
