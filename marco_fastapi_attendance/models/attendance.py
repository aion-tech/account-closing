from odoo import _, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Attendance"
    _order = "check_in desc"
