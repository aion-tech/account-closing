from odoo import api, models


class MaintenanceEquipmentCategory(models.Model):
    _name = "maintenance.equipment.category"
    _inherit = [
        "maintenance.equipment.category",
        "documents.mixin",
        "websocket.refresh.mixin",
    ]

    def _upsert_category_folder(self):
        self.ensure_one()
        Folder = self.env["documents.folder"].sudo()
        category_folder_id = Folder.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ]
        )
        if not category_folder_id:
            root_maintenance_folder_id = self.env.ref(
                "marco_maintenance.documents_maintenance_folder"
            )
            category_folder_id = Folder.create(
                {
                    "name": self.name,
                    "parent_folder_id": root_maintenance_folder_id.id,
                    "res_id": self.id,
                    "res_model": self._name,
                }
            )
        return category_folder_id

    def _get_document_folder(self):
        """
        Get equipment folder. Create if needed.
        """
        self.ensure_one()
        category_folder_id = self._upsert_category_folder()
        return category_folder_id

    def _get_document_vals(self, attachment):
        self.ensure_one()
        vals = super()._get_document_vals(attachment)
        vals["res_id"] = self.id
        vals["res_model"] = self._name
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._upsert_category_folder()
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
