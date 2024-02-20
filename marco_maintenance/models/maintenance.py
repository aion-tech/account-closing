from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_round


class DocumentsFolder(models.Model):
    _inherit = "documents.folder"

    maintenance_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Equipment",
    )


class MaintenanceEquipment(models.Model):
    _name = "maintenance.equipment"
    _inherit = [
        "maintenance.equipment",
        "documents.mixin",
    ]

    serial_no = fields.Char(
        "Serial Number",
        copy=False,
        required=True,
    )

    def _get_documents_domain(self):
        self.ensure_one()
        Folder = self.env["documents.folder"]
        folder_id = Folder.search(self._get_folder_domain())
        if folder_id:
            return [("folder_id", "=", folder_id.id)]
        else:
            return super()._get_documents_domain()

    def _get_folder_domain(self):
        self.ensure_one()
        return [("maintenance_equipment_id", "=", self.id)]

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

    def _get_document_owner(self):
        return self.env.user

    def _get_document_tags(self):
        return self.env["documents.tag"]

    def _get_document_folder(self):
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

    def _get_document_partner(self):
        return self.env["res.partner"]

    def _check_create_documents(self):
        return bool(self and self._get_document_folder())

    def _get_folder_domain(self):
        self.ensure_one()
        if not self.equipment_id:
            return super()._get_folder_domain()
        return [("maintenance_equipment_id", "=", self.equipment_id.id)]
