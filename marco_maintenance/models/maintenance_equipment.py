import uuid

from odoo import api, fields, models
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
        # default=lambda self: uuid.uuid4(),
    )

    category_id = fields.Many2one(
        required=True,
    )

    def _upsert_equipment_folder(self):
        self.ensure_one()
        Folder = self.env["documents.folder"].sudo()
        equipment_folder_id = Folder.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ]
        )
        if not equipment_folder_id:
            parent_folder = self.env["documents.folder"].search(
                self.category_id._get_folder_domain()
            )
            equipment_folder_id = Folder.create(
                {
                    "name": self.serial_no,
                    "parent_folder_id": parent_folder.id,
                    "res_id": self.id,
                    "res_model": self._name,
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

    def _get_document_vals(self, attachment):
        self.ensure_one()
        vals = super()._get_document_vals(attachment)
        vals["res_id"] = self.id
        vals["res_model"] = self._name
        return vals

    def write(self, vals):
        if "category_id" in vals:
            new_category_folder = self.env["documents.folder"].search(
                [
                    ("res_id", "=", vals["category_id"]),
                    ("res_model", "=", self.category_id._name),
                ]
            )
            equipments_folders = self.env["documents.folder"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                ]
            )
            equipments_folders.sudo().parent_folder_id = new_category_folder.id

        res = super().write(vals)
        for equipment in self:
            if "serial_no" in vals:
                folder_id = self.env["documents.folder"].search(
                    [
                        ("res_model", "=", self._name),
                        ("res_id", "=", equipment.id),
                    ]
                )
                if folder_id:
                    folder_id.name = vals["serial_no"]
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._upsert_equipment_folder()
        return res

    def copy(self, default=None):
        default = default or {}
        default["serial_no"] = uuid.uuid4()
        return super().copy(default=default)

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        # used to filter sidebar/searchpanel
        action["context"]["limit_folders_to_maintenance_resource"] = True
        return action
