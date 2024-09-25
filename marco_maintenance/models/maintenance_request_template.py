from dateutil.relativedelta import relativedelta
from odoo import _, fields, models


class MaintenanceRequestTemplate(models.Model):
    _name = "maintenance.request.template"
    _description = "Maintenance Request Template"

    name = fields.Char("Name")
    description = fields.Html("Description")
    request_name = fields.Char("Request Name")
    start_date = fields.Date(
        "Start Date",
        required=True,
    )
    end_date = fields.Date("End Date")
    period = fields.Integer("Period between each preventive maintenance")
    # period_in_days = fields.Integer(
    #     "Computed days between each preventive maintenance",
    #     compute="_compute_period_in_days",
    # )
    period_type = fields.Selection(
        string="Period Type",
        selection=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
    )
    category_id = fields.Many2one(
        string="Category",
        comodel_name="maintenance.equipment.category",
        required=True,
    )
    equipment_ids = fields.Many2many(
        string="Equipment",
        comodel_name="maintenance.equipment",
        relation="equipment_id_template_id_rel",
        column1="template_id",
        column2="equipment_id",
        domain="[('category_id', '=', category_id)]",
    )
    delta_creation_date = fields.Integer(
        string="Delta Creation Date",
        default=60,
        required=True,
    )
    maintenance_team_id = fields.Many2one(
        "maintenance.team",
        string="Maintenance Team",
        check_company=True,
        ondelete="restrict",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Technician",
        tracking=True,
    )
    duration = fields.Float(
        help="Duration in hours.",
    )

    def _compute_period_in_days(self):
        self.ensure_one()
        if self.period_type == "days":
            delta = relativedelta(days=self.period)
        elif self.period_type == "weeks":
            delta = relativedelta(weeks=self.period)
        elif self.period_type == "months":
            delta = relativedelta(months=self.period)
        elif self.period_type == "years":
            delta = relativedelta(years=self.period)
        return delta

    def open_template_form_view(self):
        return {
            "name": _("Template"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "maintenance.request.template",
            "target": "new",
            "res_id": self.id,
        }

    def _prepare_maintenance_request_vals(self, date, equipment_id: int):
        self.ensure_one()
        return {
            "name": self.request_name,
            "description": self.description,
            "request_date": date,
            "schedule_date": date,
            "category_id": self.category_id.id,
            "equipment_id": equipment_id,
            "maintenance_type": "preventive",
            "user_id": self.user_id.id,
            "maintenance_team_id": self.maintenance_team_id.id,
            "duration": self.duration,
            "company_id": self.env.company.id,
        }
