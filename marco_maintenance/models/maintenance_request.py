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
        return [
            ("res_id", "=", self.equipment_id.id),
            ("res_model", "=", self.equipment_id._name),
        ]

    def _get_document_vals(self, attachment):
        self.ensure_one()
        vals = super()._get_document_vals(attachment)
        vals["res_id"] = self.id
        vals["res_model"] = self._name
        return vals

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        # used to filter sidebar/searchpanel
        action["context"]["limit_folders_to_maintenance_resource"] = True
        return action

    def _get_documents_domain(self):
        request_domain = super()._get_documents_domain()
        equipment_domain = [
            ("res_id", "=", self.equipment_id.id),
            ("res_model", "=", self.equipment_id._name),
        ]
        return OR([request_domain, equipment_domain])
