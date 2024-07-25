from typing import Any

from odoo import api, fields, models

MAINTENANCE_MODELS = (
    "maintenance.equipment",
    "maintenance.request",
    "maintenance.equipment.category",
)


class DocumentsFolder(models.Model):
    _inherit = "documents.folder"

    res_model = fields.Char("Resource Model")
    res_id = fields.Integer("Resource ID")

    def _get_folder_name_tree(self):
        self.ensure_one()
        if self.parent_folder_id:
            names = f"{self.parent_folder_id._get_folder_name_tree()} / {self.name}"
        else:
            names = self.name
        return names


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            folder = self.env["documents.folder"].browse(val["folder_id"])

            if folder.res_model in MAINTENANCE_MODELS:
                val.update(
                    dict(
                        res_id=folder.res_id,
                        res_model=folder.res_model,
                    )
                )

        res = super().create(vals_list)

        return res

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        self = self.with_context(hierarchical_naming=False)
        ctx = self._context

        res_model = ctx.get("sidebar_res_model")
        res_id = ctx.get("sidebar_res_id")

        conditions = [
            field_name == "folder_id",
            res_model in MAINTENANCE_MODELS,
        ]

        if not all(conditions):
            return super().search_panel_select_range(field_name, **kwargs)

        folders = self.env.ref("marco_maintenance.documents_maintenance_folder")

        if res_model == "maintenance.equipment.category":
            categories = self.env[res_model].browse(res_id)
            equipments = categories.mapped("equipment_ids")
            requests = self.env["maintenance.request"].search(
                [("equipment_id", "in", equipments.ids)]
            )

        elif res_model == "maintenance.equipment":
            equipments = self.env[res_model].browse(res_id)
            categories = equipments.mapped("category_id")
            requests = self.env["maintenance.request"].search(
                [("equipment_id", "in", equipments.ids)]
            )

        elif res_model == "maintenance.request":
            requests = self.env[res_model].browse(res_id)
            equipments = requests.mapped("equipment_id")
            categories = equipments.mapped("category_id")

        domain = [
            "|",
            "|",
            "&",
            ("res_id", "in", categories.ids),
            ("res_model", "=", categories._name),
            "&",
            ("res_id", "in", equipments.ids),
            ("res_model", "=", equipments._name),
            "&",
            ("res_id", "in", requests.ids),
            ("res_model", "=", requests._name),
        ]

        folders |= self.env["documents.folder"].search(domain)

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

        res = dict(
            parent_field="parent_folder_id",
            values=values,
        )
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
        Folder = self.env["documents.folder"]
        folders = Folder.search(self._get_folder_domain())
        if folders:
            folders = Folder.search(
                [
                    "|",
                    ("id", "child_of", folders.ids),
                    ("id", "parent_of", folders.ids),
                ]
            )
        return [("folder_id", "in", folders.ids)]

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

    def _get_document_vals(self, attachment):
        self.ensure_one()
        vals = super()._get_document_vals(attachment)
        vals["res_id"] = self.id
        vals["res_model"] = self._name
        return vals

    def _upsert_folder(
        self,
        parent_folder_id: int,
        name: str,
    ):
        """
        get/create folder linked to resource `self`
        """
        self.ensure_one()
        Folder = self.env["documents.folder"].sudo()
        folder_id = Folder.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ]
        )
        if not folder_id:
            folder_id = Folder.create(
                {
                    "name": name,
                    "parent_folder_id": parent_folder_id,
                    "res_id": self.id,
                    "res_model": self._name,
                }
            )
        return folder_id

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
                    "sidebar_res_model": self._name,
                    "sidebar_res_id": self.id,
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
