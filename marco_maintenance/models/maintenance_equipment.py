from odoo import _, api, fields, models


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
