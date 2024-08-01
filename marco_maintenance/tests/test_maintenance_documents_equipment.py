import time
from datetime import date

from freezegun import freeze_time
from odoo.tests.common import tagged

from .common import MarcoMaintenanceTestCommon


@tagged("marco", "post_install", "-at_install")
class MarcoMaintenanceEquipmentTest(MarcoMaintenanceTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_create_equipment_folder_from_maintenance_request(self):
        """
        If a folder does not exist for the equipment,
        it should be created when attaching a file to
        a maintenance request using that equipment.
        """
        # Arrange
        folder_id = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )

        # make sure that the request folder exists
        request_id = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        attachment = self._attach_file_to_request(request_id)
        attachment.unlink()

        folder_id.unlink()
        self.assertFalse(folder_id.exists())

        # Assert
        self._assert_folder_structure(request_id)

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
        category_folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.category_id.id),
                ("res_model", "=", "maintenance.equipment.category"),
            ]
        )

        # Assert
        self.assertTrue(folder_id)
        self.assertEqual(folder_id.parent_folder_id, category_folder)

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
                "category_id": self.category_01.id,
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

    def test_get_documents_from_maintenance_equipment(self):
        """An equipment should see its own documents
        and all its maintenance requests documents"""
        # Arrange
        request_1 = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        request_1_attachment = self._attach_file_to_request(request_1)
        request_2 = self._create_maintenance_request(
            self.equipment_01.id,
            self.category_01.id,
        )
        request_2_attachment = self._attach_file_to_request(request_2)
        equipment_attachment = self._attach_file_to_equipment(self.equipment_01)

        # Act
        doc_ids = self.env["documents.document"].search(
            self.equipment_01._get_documents_domain()
        )

        # Assert
        self.assertTrue(doc_ids)
        self.assertEqual(len(doc_ids), 3)
        self.assertIn(
            request_1_attachment.id,
            doc_ids.mapped("attachment_id").ids,
        )
        self.assertIn(
            request_2_attachment.id,
            doc_ids.mapped("attachment_id").ids,
        )
        self.assertIn(
            equipment_attachment.id,
            doc_ids.mapped("attachment_id").ids,
        )

    def test_create_document_in_equipment_folder(self):
        """
        Equipment => documents => upload
        New documents uploaded to an equipment's folder should be
        automatically linked to the equipment
        """
        # Arrange
        folder = self.equipment_01._get_document_folder()
        ctx = self.equipment_01.action_view_documents()["context"]

        # Act
        doc = (
            self.env["documents.document"]
            .with_context(ctx)
            .create(
                {
                    "datas": self.data,
                    "name": "EquipmentAttachment",
                    "folder_id": folder.id,
                }
            )
        )

        # Assert
        self.assertEqual(doc.res_model, "maintenance.equipment")
        self.assertEqual(doc.res_id, self.equipment_01.id)

    def test_create_document_in_equipment_folder_without_context(self):
        """
        Documents => equipment folder => upload
        New documents uploaded to an equipment's folder should be
        automatically linked to the equipment
        """
        # Arrange
        folder = self.equipment_01._get_document_folder()

        # Act
        doc = self.env["documents.document"].create(
            {
                "datas": self.data,
                "name": "EquipmentAttachment",
                "folder_id": folder.id,
            }
        )

        # Assert
        self.assertEqual(doc.res_model, "maintenance.equipment")
        self.assertEqual(doc.res_id, self.equipment_01.id)

    def test_change_equipment_category(self):
        """
        When changing an equipment category, the
        equpment's folder should change its parent folder.
        """
        # Arrange
        self._attach_file_to_equipment(self.equipment_01)

        # Pre condition
        equipment_folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.equipment_01.id),
                ("res_model", "=", self.equipment_01._name),
            ]
        )
        category_01_folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.category_01.id),
                ("res_model", "=", self.category_01._name),
            ]
        )
        category_02_folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", self.category_02.id),
                ("res_model", "=", self.category_02._name),
            ]
        )
        self.assertEqual(
            equipment_folder.parent_folder_id.id,
            category_01_folder.id,
        )

        # Act
        self.equipment_01.category_id = self.category_02.id

        # Assert
        self.assertEqual(
            equipment_folder.parent_folder_id.id,
            category_02_folder.id,
        )

    @freeze_time("2024-07-01")
    def test_cron_generate_requests_no_create(self):
        # Arrange
        self.equipment_01.effective_date = date.today()
        self.equipment_01.period = 90
        self.equipment_01.delta_creation_date = 60
        self.equipment_01.maintenance_ids.unlink()

        # Act
        self.env["maintenance.equipment"]._cron_generate_requests()

        # Assert
        self.assertFalse(self.equipment_01.maintenance_ids)

    @freeze_time("2024-07-01")
    def test_cron_generate_requests_create(self):
        # Arrange
        self.equipment_01.effective_date = date.today()
        self.equipment_01.period = 90
        self.equipment_01.delta_creation_date = 90
        self.equipment_01.maintenance_ids.unlink()

        # Act
        self.env["maintenance.equipment"]._cron_generate_requests()

        # Assert
        self.assertTrue(self.equipment_01.maintenance_ids)
        self.assertEqual(len(self.equipment_01.maintenance_ids), 1)
