from odoo import _, models


class MaintenanceFolderMixin(models.AbstractModel):
    _name = "maintenance.folder.mixin"
    _description = "Maintenance Folder Mixin"

    def unlink(self):
        for rec in self:
            domain = [
                ("res_id", "=", rec.id),
                ("res_model", "=", self._name),
            ]
            folder = self.env["documents.folder"].search(domain)
            if folder:
                folder_name = folder.name
                parent_folder_name = folder.parent_folder_id.name
                (
                    self.env["documents.folder.deletion.wizard"]
                    .new({"folder_id": folder.id})
                    .delete_and_move()
                )
                documents = (
                    self.env["documents.document"]
                    .with_context(active_test=False)
                    .search(domain)
                )
                documents.write({"res_id": False, "res_model": False})

                self.env.user.notify_warning(
                    message=_(
                        f"Folder {folder_name} documents moved to parent folder {parent_folder_name}"
                    ),
                    sticky=True,
                )

        return super().unlink()
