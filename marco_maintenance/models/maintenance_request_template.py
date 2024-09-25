from typing import Literal

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MaintenanceRequestTemplate(models.Model):
    _name = "maintenance.request.template"
    _description = "Maintenance Request Template"

    name = fields.Char("Name", help="Template Name")
    description = fields.Char("Description", help="Template Description")
    request_description = fields.Html("Request Description")
    request_name = fields.Char("Request Name")
    start_date = fields.Date(
        "Start Date",
        required=True,
    )
    end_date = fields.Date("End Date")
    period = fields.Integer("Period between each preventive maintenance")
    period_type = fields.Selection(
        string="Period Type",
        selection=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
        required=True,
        default="months",
    )
    category_id = fields.Many2one(
        string="Category",
        comodel_name="maintenance.equipment.category",
        required=True,
    )
    equipment_ids_count = fields.Integer(
        "Equipments Count",
        compute="_compute_equipment_ids_count",
    )
    equipment_ids_count_and_total = fields.Char(
        "Equipments Count",
        compute="_compute_equipment_ids_count",
    )
    equipment_ids = fields.Many2many(
        string="Equipments",
        comodel_name="maintenance.equipment",
        relation="equipment_id_template_id_rel",
        column1="template_id",
        column2="equipment_id",
        domain="[('category_id', '=', category_id)]",
    )
    delta_creation_date = fields.Integer(
        string="Delta Creation Date",
        default=2,
        required=True,
    )
    delta_creation_date_period_type = fields.Selection(
        string="Period Type",
        selection=[
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
        required=True,
        default="months",
    )
    maintenance_team_id = fields.Many2one(
        "maintenance.team",
        string="Maintenance Team",
        check_company=True,
        ondelete="restrict",
    )
    technician_user_id = fields.Many2one(
        "res.users",
        string="Technician",
        tracking=True,
    )
    duration = fields.Float(
        help="Duration in hours.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    def _check_category_id_coherence(self):
        """Category should always be == equipment_ids.category"""
        for rec in self:
            is_coherent = all(
                [rec.category_id.id == eq.category_id.id for eq in rec.equipment_ids]
            )
            if not is_coherent:
                raise ValidationError(_("One or more categories are incoherent"))

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._check_category_id_coherence()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._check_category_id_coherence()
        return res

    def _compute_equipment_ids_count(self):
        for rec in self:
            selected_equipments = len(rec.equipment_ids)
            total_equipments = self.env["maintenance.equipment"].search_count(
                [("category_id", "=", rec.category_id.id)]
            )
            rec.equipment_ids_count = selected_equipments
            rec.equipment_ids_count_and_total = (
                f"{str(selected_equipments)}/{str(total_equipments)}"
            )

    def _compute_period_in_days(
        self,
        period_type: Literal["days", "weeks", "months", "years"],
        period: int,
    ) -> relativedelta:
        self.ensure_one()
        if period_type == "days":
            delta = relativedelta(days=period)
        elif period_type == "weeks":
            delta = relativedelta(weeks=period)
        elif period_type == "months":
            delta = relativedelta(months=period)
        elif period_type == "years":
            delta = relativedelta(years=period)
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
            "description": self.request_description,
            "request_date": date,
            "schedule_date": date,
            "category_id": self.category_id.id,
            "equipment_id": equipment_id,
            "maintenance_type": "preventive",
            "user_id": self.technician_user_id.id,
            "maintenance_team_id": self.maintenance_team_id.id,
            "duration": self.duration,
            "company_id": self.env.company.id,
            "template_id": self.id,
        }
