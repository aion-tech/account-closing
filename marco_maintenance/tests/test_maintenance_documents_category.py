from odoo.tests.common import tagged

from .common import MarcoMaintenanceTestCommon


@tagged("marco", "post_install", "-at_install")
class MarcoMaintenanceCategoryTest(MarcoMaintenanceTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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

    def test_unlink_category_move_documents(self):
        # Arrange
        attachment0 = self._attach_file_to_category(self.category_01)
        attachment1 = self._attach_file_to_category(self.category_01)
        documents = self.env["documents.document"].search(
            [
                ("res_id", "in", [attachment0.res_id, attachment1.res_id]),
                ("res_model", "=", "maintenance.equipment.category"),
            ]
        )
        folder = documents.folder_id
        parent_folder = folder.parent_folder_id

        # Act
        self.category_01.equipment_ids.unlink()
        self.category_01.unlink()

        # Assert
        self.assertTrue(documents.exists())
        self.assertEqual(len(documents.exists()), 2)
        self.assertEqual(documents.folder_id.id, parent_folder.id)
        self.assertFalse(folder.exists())
