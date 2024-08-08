from odoo import models
from odoo.models import BaseModel

REFRESHABLE_MODELS = [
    "maintenance.request",
    "maintenance.equipment",
    "maintenance.equipment.category",
]


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _create_document(self, vals):
        res = super()._create_document(vals)
        res_model = vals.get("res_model")
        if res_model in REFRESHABLE_MODELS:
            to_refresh_id = self.env[res_model].browse(vals.get("res_id"))
            to_refresh_id.websocket_refresh()
        return res

    def unlink(self):
        to_refresh_ids: dict[str, BaseModel] = {
            model: self.env[model] for model in REFRESHABLE_MODELS
        }
        attachments_to_refresh = self.filtered(
            lambda att: att.res_model in REFRESHABLE_MODELS
        )
        for attachment in attachments_to_refresh:
            record_to_refresh = self.env[attachment.res_model].browse(
                attachments_to_refresh.mapped("res_id")
            )
            to_refresh_ids[attachment.res_model] |= record_to_refresh
        res = super().unlink()
        if to_refresh_ids:
            for model, records in to_refresh_ids.items():
                records.websocket_refresh()
        return res
