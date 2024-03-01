from odoo import _, api, fields, models


class DocumentsFolder(models.Model):
    _inherit = "documents.folder"

    maintenance_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Equipment",
    )


class DocumentMixin(models.AbstractModel):
    _inherit = "documents.mixin"

    documents_count = fields.Integer(
        "Documents",
        compute="_compute_documents_count",
    )

    def _get_documents_domain(self):
        """
        return a domain used to find the documents linked
        kto singleton `self`.
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

    def _get_document_ids(self):
        """Return a documents.document recordset linked to singleton `self`."""
        self.ensure_one()
        return self.env["documents.document"].search(self._get_documents_domain())

    def action_view_documents(self):
        """
        Return an aciton view to display documents linked
        to singleton `self` in the Documents app.
        """
        self.ensure_one()
        tree_view_id = self.env.ref("documents.documents_view_list").id
        kanban_view_id = self.env.ref("documents.document_view_kanban").id
        Folder = self.env["documents.folder"]
        folder_id = Folder.search(self._get_folder_domain())
        ctx = self.env.context.copy()
        if folder_id:
            ctx.update({"searchpanel_default_folder_id": folder_id.id})

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
