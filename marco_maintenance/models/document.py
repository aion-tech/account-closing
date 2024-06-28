from typing import Any, Dict, List

from odoo import _, api, fields, models
from odoo.osv.expression import OR


class DocumentsFolder(models.Model):
    _inherit = "documents.folder"

    maintenance_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Equipment",
    )


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    maintenance_request_id = fields.Many2one(
        "maintenance.request",
        string="Maintenance Request",
    )
    maintenance_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Equipment",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            folder = self.env["documents.folder"].browse(val["folder_id"])
            equipment = folder.maintenance_equipment_id
            keys = [
                "res_model",
                "res_id",
            ]
            if (
                equipment
                and all([k not in val for k in keys])
                and "maintenance_request_id" not in val
            ):
                val.update(
                    dict(
                        res_id=equipment.id,
                        res_model="maintenance.equipment",
                    )
                )
        res = super().create(vals_list)

        return res

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        res_model = self._context.get("active_model")
        domain = kwargs.get("search_domain")
        conditions = [
            field_name == "folder_id",
            self._context.get("limit_folders_to_maintenance_resource"),
            res_model in ("maintenance.equipment", "maintenance.request"),
            domain,
        ]

        if not all(conditions):
            return super().search_panel_select_range(field_name, **kwargs)

        folders = self.env["documents.document"].search(domain).mapped(
            "folder_id"
        ) | self.env.ref("marco_maintenance.documents_maintenance_folder")

        if res_model == "maintenance.equipment":
            folders |= self.env["documents.folder"].search(
                [("maintenance_equipment_id", "in", self._context["active_ids"])]
            )
        elif res_model == "maintenance.request":
            requests = self.env["maintenance.request"].browse(
                self._context["active_ids"]
            )
            equipments = requests.mapped("equipment_id")
            if equipments:
                folders |= self.env["documents.folder"].search(
                    [("maintenance_equipment_id", "in", equipments.ids)]
                )

        folders_data = folders.read(
            fields=[
                "company_id",
                "description",
                "display_name",
                "has_write_access",
                "id",
                "parent_folder_id",
            ]
        )

        values: List[Dict[str, Any]] = []
        for fd in folders_data:
            if fd.get("parent_folder_id"):
                fd["parent_folder_id"] = fd["parent_folder_id"][0]
            else:
                fd["parent_folder_id"] = False
            values.append(fd)
        res = dict(parent_field="parent_folder_id", values=values)
        return res


class DocumentMixin(models.AbstractModel):
    _inherit = "documents.mixin"

    documents_count = fields.Integer(
        "Documents",
        compute="_compute_documents_count",
    )
    folder_exists = fields.Boolean(
        help="Folder exists for this resource",
        compute="_compute_folder_exists",
    )

    def _get_documents_domain(self):
        """
        return a domain used to find the documents linked
        to singleton `self`.
        The default implementation is likely to be enough.
        """
        self.ensure_one()
        return [("res_model", "=", self._name), ("res_id", "=", self.id)]

    def _get_folder_domain(self):
        """
        Return a domain used to find the folder linked
        to documents linked to singleton `self`.
        When using the default no folders will be found.
        """
        self.ensure_one()
        return [("1", "=", False)]

    def _compute_documents_count(self):
        for rec in self:
            rec.documents_count = self.env["documents.document"].search_count(
                self._get_documents_domain()
            )

    def _compute_folder_exists(self):
        for rec in self:
            rec.folder_exists = bool(
                self.env["documents.folder"].search(rec._get_folder_domain())
            )

    def _get_document_ids(self):
        """Return a documents.document recordset linked to singleton `self`."""
        self.ensure_one()
        return self.env["documents.document"].search(self._get_documents_domain())

    def action_view_documents(self):
        """
        Return an action view to display documents linked
        to singleton `self` in the Documents app.
        """
        self.ensure_one()
        tree_view_id = self.env.ref("documents.documents_view_list").id
        kanban_view_id = self.env.ref("documents.document_view_kanban").id
        Folder = self.env["documents.folder"]
        folder_id = Folder.search(self._get_folder_domain())
        ctx = self.env.context.copy()
        if folder_id:
            ctx.update(
                {
                    "searchpanel_default_folder_id": folder_id.id,
                    "default_res_model": self._name,
                    "default_res_id": self.id,
                }
            )

        return {
            "type": "ir.actions.act_window",
            "res_model": "documents.document",
            "name": f"{self.name} Documents",
            "view_mode": "kanban,tree,form",
            "views": [
                (kanban_view_id, "kanban"),
                (tree_view_id, "tree"),
                (False, "form"),
            ],
            "context": ctx,
        }
