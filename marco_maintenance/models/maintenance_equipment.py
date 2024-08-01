import uuid
from datetime import timedelta

from odoo import api, fields, models


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

    category_id = fields.Many2one(
        required=True,
    )

    delta_creation_date = fields.Integer(
        string="Delta Creation Date",
        default=60,
        required=True,
    )

    @api.model
    def _cron_generate_requests(self):
        """
        Generates maintenance request on the
        next_action_date or today if none exists
        """
        date_now = fields.Date.context_today(self)

        for equipment in self.search([("period", ">", 0)]):
            # Calculate the check date as
            # next_action_date - delta_creation_date
            check_date = equipment.next_action_date - timedelta(
                days=equipment.delta_creation_date
            )

            # Check if today's date is greater than or equal to check_date
            if date_now >= check_date or not equipment.delta_creation_date:
                next_requests = self.env["maintenance.request"].search(
                    [
                        ("stage_id.done", "=", False),
                        ("equipment_id", "=", equipment.id),
                        ("maintenance_type", "=", "preventive"),
                        ("request_date", "=", equipment.next_action_date),
                    ]
                )
                if not next_requests:
                    equipment._create_new_request(equipment.next_action_date)

    def _get_document_folder(self):
        """
        Get equipment folder. Create if needed.
        """
        self.ensure_one()
        parent_folder = self.category_id._get_document_folder()
        return self._upsert_folder(parent_folder.id, self.serial_no)

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
        parent_folder = self.env["documents.folder"].search(
            res.category_id._get_folder_domain()
        )
        res._upsert_folder(parent_folder.id, res.serial_no)
        return res

    def copy(self, default=None):
        default = default or {}
        default["serial_no"] = uuid.uuid4()
        return super().copy(default=default)

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        return action
