from odoo import _, api, fields, models
from odoo.osv.expression import OR


class MaintenanceRequest(models.Model):
    _name = "maintenance.request"
    _inherit = [
        "maintenance.request",
        "documents.mixin",
        "websocket.refresh.mixin",
    ]

    equipment_id = fields.Many2one(
        required=True,
    )

    def _get_document_folder(self):
        """
        Get a request's equipment folder.
        Create if needed.
        """
        self.ensure_one()
        equipment_folder_id = self.equipment_id._get_document_folder()
        return equipment_folder_id

    def _get_folder_domain(self):
        self.ensure_one()
        if not self.equipment_id:
            return super()._get_folder_domain()
        return [("maintenance_equipment_id", "=", self.equipment_id.id)]

    def _get_document_vals(self, attachment):
        self.ensure_one()
        vals = super()._get_document_vals(attachment)
        vals["maintenance_request_id"] = self.id
        return vals

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        return action

    def _get_documents_domain(self):
        request_domain = super()._get_documents_domain()
        equipment_domain = [("maintenance_equipment_id", "=", self.equipment_id.id)]
        return OR([request_domain, equipment_domain])
