from odoo import api, models


class MaintenanceEquipmentCategory(models.Model):
    _name = "maintenance.equipment.category"
    _inherit = [
        "maintenance.equipment.category",
        "documents.mixin",
        "websocket.refresh.mixin",
        "maintenance.folder.mixin",
    ]

    def _get_document_folder(self):
        """
        Get equipment folder. Create if needed.
        """
        self.ensure_one()
        parent_folder_id = self.env.ref(
            "marco_maintenance.documents_maintenance_folder"
        )
        return self._upsert_folder(parent_folder_id.id, self.name)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        parent_folder_id = self.env.ref(
            "marco_maintenance.documents_maintenance_folder"
        )
        res._upsert_folder(parent_folder_id.id, res.name)
        return res

    def write(self, vals):
        res = super().write(vals)
        for category in self:
            if "name" in vals:
                folder_id = self.env["documents.folder"].search(
                    [
                        ("res_model", "=", self._name),
                        ("res_id", "=", category.id),
                    ]
                )
                if folder_id:
                    folder_id.name = vals["name"]
        return res
