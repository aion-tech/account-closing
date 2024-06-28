import time

from odoo.tests.common import TransactionCase, tagged

from .common import MarcoMaintenanceTestCommon

DATA = "data:application/zip;base64,R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="


@tagged("marco")
class MarcoMaintenanceTest(MarcoMaintenanceTestCommon):
    def setUp(self):
        super().setUp()
        self.root_folder_id = self.env.ref(
            "marco_maintenance.documents_maintenance_folder"
        )

    def _attach_file_to_equipment(self, equipment):
        equipment_attachment = self.env["ir.attachment"].create(
            {
                "datas": DATA,
                "name": "EquipmentAttachment",
                "res_model": "maintenance.equipment",
                "res_id": equipment.id,
            }
        )
        return equipment_attachment

    def _attach_file_to_request(self, request):
        # attach file
        attachment = self.env["ir.attachment"].create(
            {
                "datas": DATA,
                "name": "DataDataData",
                "res_model": "maintenance.request",
                "res_id": request.id,
            }
        )
        return attachment

    def _create_maintenance_request(self):
        request_id = self.maintenance_request.with_user(self.user).create(
            {
                "name": "Resolution is bad",
                "user_id": self.user.id,
                "owner_user_id": self.user.id,
                "equipment_id": self.equipment_01.id,
                "color": 7,
                "stage_id": self.ref("maintenance.stage_0"),
                "maintenance_team_id": self.ref(
                    "maintenance.equipment_team_maintenance"
                ),
            }
        )
        return request_id

    def _assert_folder_structure(self, request_id):
        folder_id = request_id._get_document_folder()
        self.assertTrue(folder_id)
        self.assertEqual(
            folder_id.parent_folder_id,
            self.root_folder_id,
        )
        self.assertEqual(
            folder_id.res_id,
            request_id.equipment_id.id,
        )
        self.assertEqual(
            folder_id.res_model,
            "maintenance.equipment",
        )

    def test_get_folder(self):
        """
        If a folder exists for the equipment, it should be found
        when attaching a file to the maintenance request.
        """
        # Pre-condition
        folder_id = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )
        self.assertTrue(folder_id)

        # Act
        request_id = self._create_maintenance_request()
        self._attach_file_to_request(request_id)
        request_folder_id = request_id._get_document_folder()

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(request_folder_id.id == folder_id.id)

    def test_create_folder_from_maintenance_request(self):
        """
        If a folder does not exist for the equipment,
        it should be created when attaching a file to
        a maintenance request using that equipment.
        """
        # Pre-condition
        folder_id = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )
        folder_id.unlink()
        self.assertFalse(folder_id.exists())

        # Arrange
        request_id = self._create_maintenance_request()
        self._attach_file_to_request(request_id)

        # Act
        folder_id = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(folder_id)
        self.assertEqual(folder_id.parent_folder_id, self.root_folder_id)

    def test_create_folder_from_maintenance_equipment(self):
        """
        If a folder does not exist for the equipment,
        it should be created when attaching a file to
        a maintenance equipment.
        """
        # Pre-condition
        folder_id = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )
        folder_id.unlink()
        self.assertFalse(folder_id.exists())

        # Arrange
        self._attach_file_to_equipment(self.equipment_01)

        # Act
        folder_id = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )

        # Assert
        self.assertTrue(folder_id)
        self.assertEqual(folder_id.parent_folder_id, self.root_folder_id)

    def test_create_folder_at_equipment_creation(self):
        """
        When creating a new equipment, the equipment's
        folder should be automatically created.
        """
        # Arrange
        # Act
        equipment = self.equipment.create(
            {
                "name": "My new equipment",
                "category_id": self.equipment_monitor.id,
                "technician_user_id": self.ref("base.user_root"),
                "owner_user_id": self.user.id,
                "assign_date": time.strftime("%Y-%m-%d"),
                "serial_no": "XXYYZZ",
                "model": "ABCABCABC",
                "color": 2,
            }
        )
        folder = self.env["documents.folder"].search(
            [
                ("res_model", "=", equipment._name),
                ("res_id", "=", equipment.id),
            ]
        )

        # Assert
        self.assertTrue(folder)

    def test_get_documents_from_maintenance_request(self):
        """A maintenance request should see its own documents"""
        # Arrange
        request_id = self._create_maintenance_request()
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

    def test_get_documents_from_maintenance_request_with_equipment_documents(self):
        """A maintenance request should see its own
        documents and the equipment documents"""
        # Arrange
        request_id = self._create_maintenance_request()
        request_attachment = self._attach_file_to_request(request_id)
        equipment_attachment = self._attach_file_to_equipment(self.equipment_01)

        # Act
        doc_ids = self.env["documents.document"].search(
            request_id._get_documents_domain()
        )

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(doc_ids)
        self.assertEqual(len(doc_ids), 2)
        self.assertIn(equipment_attachment.id, doc_ids.mapped("attachment_id").ids)
        self.assertIn(request_attachment.id, doc_ids.mapped("attachment_id").ids)

    def test_get_documents_from_sibling_maintenance_request(self):
        """Maintenance requests not see sibling maintenance requests docs."""
        # Arrange
        request_1 = self._create_maintenance_request()
        request_1_attachment = self._attach_file_to_request(request_1)
        request_2 = self._create_maintenance_request()
        request_2_attachment = self._attach_file_to_request(request_2)
        equipment_attachment = self._attach_file_to_equipment(self.equipment_01)

        # Act
        doc_ids = self.env["documents.document"].search(
            request_1._get_documents_domain()
        )

        # Assert
        self.assertTrue(doc_ids)
        self.assertEqual(len(doc_ids), 2)
        self.assertIn(request_1_attachment.id, doc_ids.mapped("attachment_id").ids)
        self.assertIn(equipment_attachment.id, doc_ids.mapped("attachment_id").ids)
        self.assertNotIn(request_2_attachment.id, doc_ids.mapped("attachment_id").ids)

    def test_get_documents_from_maintenance_equipment(self):
        """An equipment should see its own documents
        and all its maintenance requests documents"""
        # Arrange
        request_1 = self._create_maintenance_request()
        request_1_attachment = self._attach_file_to_request(request_1)
        request_2 = self._create_maintenance_request()
        request_2_attachment = self._attach_file_to_request(request_2)
        equipment_attachment = self._attach_file_to_equipment(self.equipment_01)

        # Act
        doc_ids = self.env["documents.document"].search(
            self.equipment_01._get_documents_domain()
        )

        # Assert
        self.assertTrue(doc_ids)
        self.assertEqual(len(doc_ids), 3)
        self.assertIn(request_1_attachment.id, doc_ids.mapped("attachment_id").ids)
        self.assertIn(request_2_attachment.id, doc_ids.mapped("attachment_id").ids)
        self.assertIn(equipment_attachment.id, doc_ids.mapped("attachment_id").ids)

    def test_create_document_in_request_folder(self):
        # Arrange
        request = self._create_maintenance_request()
        folder = self.env["documents.folder"].search(request._get_folder_domain())
        ctx = request.action_view_documents()["context"]

        # Act
        doc = self.env["documents.document"].create(
            {
                "datas": DATA,
                "name": "EquipmentAttachment",
                "folder_id": folder.id,
                "res_model": ctx["default_res_model"],
                "res_id": ctx["default_res_id"],
            }
        )

        # Assert
        self.assertEqual(doc.res_model, "maintenance.request")
        self.assertEqual(doc.res_id, request.id)

    def test_create_document_in_equipment_folder(self):
        # Arrange
        folder = self.equipment_01._get_document_folder()
        ctx = self.equipment_01.action_view_documents()["context"]

        # Act
        doc = (
            self.env["documents.document"]
            .with_context(ctx)
            .create(
                {
                    "datas": DATA,
                    "name": "EquipmentAttachment",
                    "folder_id": folder.id,
                }
            )
        )

        # Assert
        self.assertEqual(doc.res_model, "maintenance.equipment")
        self.assertEqual(doc.res_id, self.equipment_01.id)

    def test_create_document_in_equipment_folder_without_context(self):
        # Arrange
        folder = self.equipment_01._get_document_folder()

        # Act
        doc = self.env["documents.document"].create(
            {
                "datas": DATA,
                "name": "EquipmentAttachment",
                "folder_id": folder.id,
            }
        )

        # Assert
        self.assertEqual(doc.res_model, "maintenance.equipment")
        self.assertEqual(doc.res_id, self.equipment_01.id)
