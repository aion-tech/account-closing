from odoo import fields, models


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
        Get a request's folder.
        """
        self.ensure_one()
        parent_folder = self.equipment_id._get_document_folder()
        return self._upsert_folder(parent_folder.id, self.name)

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        return action

    def action_view_equipment_documents(self):
        """
        Return an action view to display documents linked
        to equipments linked to singleton `self` in the Documents app.
        """
        action = self.action_view_documents()
        action["domain"] = self.equipment_id._get_documents_domain()
        action["context"]["default_res_id"] = self.equipment_id.id
        action["context"]["default_res_model"] = "maintenance.equipment"
        action["context"]["searchpanel_default_folder_id"] = (
            self.equipment_id._get_document_folder().id
        )
        return action

    def write(self, vals):
        res = super().write(vals)
        if "equipment_id" in vals:
            folder = self.env["documents.folder"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                ]
            )
            equipment = self.env["maintenance.equipment"].browse(vals["equipment_id"])
            equipment_folder = equipment._get_document_folder()
            folder.sudo().parent_folder_id = equipment_folder.id
        return res
