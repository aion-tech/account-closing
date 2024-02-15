from odoo import api, fields, models


class DocumentMixin(models.AbstractModel):
    _inherit = "documents.mixin"

    documents_count = fields.Integer(
        "Documents",
        compute="_compute_documents_count",
    )

    def _get_documents_domain(self):
        self.ensure_one()
        return [("res_model", "=", self._name), ("res_id", "=", self.id)]

    def _get_folder_domain(self):
        self.ensure_one()
        return [("1", "=", False)]

    def _compute_documents_count(self):
        for equipment in self:
            equipment.documents_count = self.env["documents.document"].search_count(
                self._get_documents_domain()
            )

    def action_view_documents(self):
        self.ensure_one()
        tree_view_id = self.env.ref("documents.documents_view_list").id
        Folder = self.env["documents.folder"]
        Document = self.env["documents.document"]
        folder_id = Folder.search(self._get_folder_domain())
        document_ids = Document.search(self._get_documents_domain())
        ctx = self.env.context.copy()
        if folder_id:
            ctx.update({"searchpanel_default_folder_id": folder_id.ids})

        return {
            "type": "ir.actions.act_window",
            "res_model": "documents.document",
            "domain": [("id", "=", document_ids.ids)],
            "name": f"{self.name} Documents",
            "view_mode": "tree,form,kanban",
            "views": [(tree_view_id, "tree"), (False, "form"), (False, "kanban")],
            "context": ctx,
        }
