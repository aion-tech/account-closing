from odoo import _, api, fields, models


class MaintenanceRequest(models.Model):
    _name = "maintenance.request"
    _inherit = [
        "maintenance.request",
        "documents.mixin",
        "websocket.refresh.mixin",
    ]

    equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Equipment",
        ondelete="restrict",
        index=True,
        required=True,
    )

    def _get_document_folder(self):
        """
        Get a request's equipment folder.
        Create if needed.
        """
        self.ensure_one()
        Folder = self.env["documents.folder"]
        root_maintenance_folder_id = self.env.ref(
            "marco_maintenance.documents_maintenance_folder"
        )

        equipment_folder_id = Folder.search(
            [("maintenance_equipment_id", "=", self.equipment_id.id)]
        )
        if not equipment_folder_id:
            equipment_folder_id = self.env["documents.folder"].create(
                {
                    "name": self.equipment_id.serial_no,
                    "parent_folder_id": root_maintenance_folder_id.id,
                    "maintenance_equipment_id": self.equipment_id.id,
                }
            )
        return equipment_folder_id

    def _get_folder_domain(self):
        self.ensure_one()
        if not self.equipment_id:
            return super()._get_folder_domain()
        return [("maintenance_equipment_id", "=", self.equipment_id.id)]
