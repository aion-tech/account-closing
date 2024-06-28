from odoo.tests.common import tagged

from .common import MarcoMaintenanceTestCommon

DATA = "data:application/zip;base64,R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="


@tagged("marco", "post_install", "-at_install")
class MarcoMaintenanceCategoryTest(MarcoMaintenanceTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root_folder_id = cls.env.ref(
            "marco_maintenance.documents_maintenance_folder"
        )

    def test_create_category_create_folder(self):
        """
        Creating a new category should create its folder
        """
        # Arrange

        # Act
        category = self.env["maintenance.equipment.category"].create(
            dict(name="my category")
        )
        folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", category.id),
                ("res_model", "=", category._name),
            ]
        )

        # Assert
        self.assertTrue(folder)
