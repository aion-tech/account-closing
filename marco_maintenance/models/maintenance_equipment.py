from odoo import _, api, fields, models
from odoo.osv.expression import AND


class MaintenanceEquipment(models.Model):
    _name = "maintenance.equipment"
    _inherit = [
        "maintenance.equipment",
        "documents.mixin",
        "websocket.refresh.mixin",
    ]

    serial_no = fields.Char(
        "Serial Number",
        copy=False,
        required=True,
    )

    def _upsert_equipment_folder(self):
        self.ensure_one()
        Folder = self.env["documents.folder"].sudo()
        equipment_folder_id = Folder.search(
            [("maintenance_equipment_id", "=", self.id)]
        )
        if not equipment_folder_id:
            root_maintenance_folder_id = self.env.ref(
                "marco_maintenance.documents_maintenance_folder"
            )
            equipment_folder_id = Folder.create(
                {
                    "name": self.serial_no,
                    "parent_folder_id": root_maintenance_folder_id.id,
                    "maintenance_equipment_id": self.id,
                }
            )
        return equipment_folder_id

    def _get_document_folder(self):
        """
        Get equipment folder. Create if needed.
        """
        self.ensure_one()
        equipment_folder_id = self._upsert_equipment_folder()
        return equipment_folder_id

    def _get_documents_domain(self):
        self.ensure_one()
        domain = AND(
            [
                self._get_folder_domain(),
            ]
        )
        Folder = self.env["documents.folder"]
        # parent folder
        folders = Folder.search(domain)
        if folders:
            # children folders
            children_folders = Folder.search([("id", "child_of", folders.id)])
            folders |= children_folders
            return [("folder_id", "in", folders.ids)]

        else:
            return super()._get_documents_domain()

    def _get_folder_domain(self):
        self.ensure_one()
        return [("maintenance_equipment_id", "=", self.id)]

    def _get_document_vals(self, attachment):
        self.ensure_one()
        vals = super()._get_document_vals(attachment)
        vals["maintenance_equipment_id"] = self.id
        return vals

    def write(self, vals):
        res = super(MaintenanceEquipment, self).write(vals)
        for equipment in self:
            if "serial_no" in vals:
                folder_id = self.env["documents.folder"].search(
                    [("maintenance_equipment_id", "=", equipment.id)]
                )
                if folder_id:
                    folder_id.name = vals["serial_no"]
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._upsert_equipment_folder()
        return res

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        # used to filter sidebar/searchpanel
        action["context"]["limit_folders_to_maintenance_resource"] = True
        return action
