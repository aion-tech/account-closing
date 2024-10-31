from odoo import Command, api, fields, models
from odoo.tools import safe_eval


class MaintenancePlan(models.Model):
    _inherit = "maintenance.plan"

    equipment_ids = fields.Many2many(
        string="Equipments",
        comodel_name="maintenance.equipment",
        compute="_set_equipment_ids",
        inverse="_set_generate_domain",
    )
    generate_domain = fields.Char(
        compute="_set_generate_domain",
        inverse="_set_equipment_ids",
        store=True,
    )
    request_name = fields.Char(
        "Request Name",
    )
    technician_user_id = fields.Many2one(
        "res.users",
        string="Technician",
        tracking=True,
    )

    @api.depends("generate_domain")
    def _set_equipment_ids(self):
        for rec in self:
            if not rec.generate_domain:
                rec.equipment_ids = False
                continue

            domain = safe_eval.safe_eval(
                rec.generate_domain,
                rec._get_eval_context(),
            )
            equipment_ids = self.env["maintenance.equipment"].search(domain)
            rec.equipment_ids = [Command.set(equipment_ids.ids)]

    @api.depends("equipment_ids")
    def _set_generate_domain(self):
        for rec in self:
            if not rec.equipment_ids:
                rec.generate_domain = '[("id", "=", False)]'
                continue

            current_categories = rec.equipment_ids.mapped("category_id")
            current_serial_nos = rec.equipment_ids.mapped("serial_no")
            rec.generate_domain = [
                ("serial_no", "in", current_serial_nos),
                ("category_id", "in", current_categories.ids),
            ]

    @api.onchange("generate_with_domain")
    def _onchange_generate_with_domain(self):
        if self.generate_with_domain:
            self.equipment_id = False
        else:
            self.generate_domain = '[("id", "=", False)]'
