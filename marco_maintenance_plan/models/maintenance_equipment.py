from odoo import models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    def _prepare_request_from_plan(self, maintenance_plan, next_maintenance_date):
        data = super()._prepare_request_from_plan(
            maintenance_plan,
            next_maintenance_date,
        )
        data["name"] = (
            maintenance_plan.request_name
            and maintenance_plan.request_name
            or data["name"]
        )
        data["user_id"] = (
            maintenance_plan.technician_user_id
            and maintenance_plan.technician_user_id.id
            or data["user_id"]
        )
        return data
