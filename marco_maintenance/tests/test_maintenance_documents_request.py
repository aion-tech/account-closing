from odoo.tests.common import tagged

from .common import MarcoMaintenanceTestCommon


@tagged("marco", "post_install", "-at_install")
class MarcoMaintenanceTestRequest(MarcoMaintenanceTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_documents_from_maintenance_request(self):
        """A maintenance request should see its own documents"""
        # Arrange
        request_id = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        attachment = self._attach_file_to_request(request_id)

        # Act
        doc_id = self.env["documents.document"].search(
            request_id._get_documents_domain()
        )

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(doc_id)
        self.assertEqual(len(doc_id), 1)
        self.assertEqual(doc_id.attachment_id.id, attachment.id)

    def test_request_folder_exist(self):
        """
        When creating a new request no folder should be created.
        When attaching a document to a request, a folder should be created.
        """
        # Arrange

        # Act
        request = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        folder = self.env["documents.folder"].search(request._get_folder_domain())
        self.assertFalse(folder)
        self._attach_file_to_request(request)

        # Assert
        folder = self.env["documents.folder"].search(request._get_folder_domain())
        self.assertTrue(folder)

    def test_create_document_in_request_folder(self):
        """
        request => documents => upload
        should automatically link the newly uploaded
        document to the maintenance request
        """
        # Arrange
        request = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        self._attach_file_to_request(request)
        folder = self.env["documents.folder"].search(request._get_folder_domain())
        ctx = request.action_view_documents()["context"]
        # Act
        doc = self.env["documents.document"].create(
            {
                "datas": self.data,
                "name": "EquipmentAttachment",
                "folder_id": folder.id,
                "res_model": ctx["default_res_model"],
                "res_id": ctx["default_res_id"],
            }
        )

        # Assert
        self.assertEqual(doc.res_model, "maintenance.request")
        self.assertEqual(doc.res_id, request.id)

    def test_change_request_equipment(self):
        """
        When changing a request equipment, the request folder
        should have the new equipment's folder as parent
        """
        # Arrange
        request = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        attachment = self._attach_file_to_request(request)
        document = self.env["documents.document"].search(
            [
                ("res_id", "=", attachment.res_id),
                ("res_model", "=", attachment.res_model),
            ]
        )

        # Act
        request.equipment_id = self.equipment_02
        equipment_folder = self.env["documents.folder"].search(
            request.equipment_id._get_folder_domain(),
        )

        # Assert
        self.assertEqual(
            document.folder_id.parent_folder_id.id,
            equipment_folder.id,
        )
