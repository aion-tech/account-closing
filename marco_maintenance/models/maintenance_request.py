from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    _name = "maintenance.request"
    _inherit = [
        "maintenance.request",
        "documents.mixin",
        "websocket.refresh.mixin",
        "maintenance.folder.mixin",
    ]

    equipment_id = fields.Many2one(
        required=True,
    )

    name_sequence = fields.Char(
        "Request Number",
        readonly=True,
    )
    template_id = fields.Many2one(
        string="Template",
        comodel_name="maintenance.request.template",
    )

    def _get_document_folder(self):
        """
        Get a request's folder.
        """
        self.ensure_one()
        parent_folder = self.equipment_id._get_document_folder()
        return self._upsert_folder(parent_folder.id, self.name_sequence)

    def action_view_documents(self):
        action = super().action_view_documents()
        action["domain"] = self._get_documents_domain()
        return action

    def action_view_equipment_documents(self):
        """
        Return an action view to display documents linked
        to equipments linked to singleton `self` in the Documents app.
        """
        action = self.action_view_documents()
        action["domain"] = self.equipment_id._get_documents_domain()
        action["context"]["sidebar_res_id"] = self.equipment_id.id
        action["context"]["sidebar_res_model"] = "maintenance.equipment"
        action["context"]["searchpanel_default_folder_id"] = (
            self.equipment_id._get_document_folder().id
        )
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            # reset next sequence based on current month
            sequence = self.env.ref(
                "marco_maintenance.marco_maintenance_request_sequence"
            )
            last_request = self.search([], limit=1, order="create_date desc")
            if last_request:
                if last_request.create_date.month != fields.Date.today().month:
                    sequence.number_next_actual = 1
            else:
                sequence.number_next_actual = 1

            next_sequence = sequence.next_by_code("maintenance.sequence")
            val["name_sequence"] = next_sequence

        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "equipment_id" in vals:
            folder = self.env["documents.folder"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                ]
            )
            equipment = self.env["maintenance.equipment"].browse(vals["equipment_id"])
            equipment_folder = equipment._get_document_folder()
            folder.sudo().parent_folder_id = equipment_folder.id
        return res
