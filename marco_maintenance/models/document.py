from typing import Any

from odoo import api, fields, models


class DocumentsFolder(models.Model):
    _inherit = "documents.folder"

    res_model = fields.Char("Resource Model")
    res_id = fields.Integer("Resource ID")


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            folder = self.env["documents.folder"].browse(val["folder_id"])
            keys = [
                "res_model",
                "res_id",
            ]
            if folder.res_model == "maintenance.equipment" and all(
                [k not in val for k in keys]
            ):
                val.update(
                    dict(
                        res_id=folder.res_id,
                        res_model="maintenance.equipment",
                    )
                )
        res = super().create(vals_list)

        return res

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        ctx = self._context
        params = ctx.get("params")
        if not params:
            params = dict(
                model=ctx.get("active_model"),
                id=ctx.get("active_id"),
            )
        res_model = params.get("model")

        conditions = [
            field_name == "folder_id",
            res_model in ("maintenance.equipment", "maintenance.request"),
        ]

        if not all(conditions):
            return super().search_panel_select_range(field_name, **kwargs)

        if res_model == "maintenance.equipment":
            equipments = self.env[res_model].browse(params["id"])

        elif res_model == "maintenance.request":
            requests = self.env[res_model].browse(params["id"])
            equipments = requests.mapped("equipment_id")

        folders = self.env["documents.folder"].search(
            [
                "&",
                ("res_id", "in", equipments.ids),
                ("res_model", "=", equipments._name),
            ]
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

        values: list[dict[str, Any]] = []
        for fd in folders_data:
            if fd.get("parent_folder_id"):
                fd["parent_folder_id"] = fd["parent_folder_id"][0]
            else:
                fd["parent_folder_id"] = False
            values.append(fd)

        res = dict(values=values)
        return res

    def clone_xlsx_into_spreadsheet(self):
        res = super().clone_xlsx_into_spreadsheet()
        new_doc = self.browse(res)
        new_doc.write(
            dict(
                res_id=self.res_id,
                res_model=self.res_model,
            )
        )
        self.unlink()
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
        return [
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
        ]

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
