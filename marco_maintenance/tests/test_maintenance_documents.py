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
        # attach file
        self.env["ir.attachment"].create(
            {
                "datas": DATA,
                "name": "DataDataData",
                "res_model": "maintenance.request",
                "res_id": request_id.id,
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
            folder_id.maintenance_equipment_id.id,
            request_id.equipment_id.id,
        )

    def test_get_folder(self):
        """
        If a foder exists for the equipment, it should be found
        when attaching a file to the maintenance request.
        """
        # Arrange
        folder_id = self.env["documents.folder"].create(
            {
                "name": self.equipment_01.name,
                "maintenance_equipment_id": self.equipment_01.id,
                "parent_folder_id": self.root_folder_id.id,
            }
        )

        # Act
        request_id = self._create_maintenance_request()
        request_folder_id = request_id._get_document_folder()

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(request_folder_id.id == folder_id.id)

    def test_create_folder(self):
        """
        If a folder does not exist for the equipment,
        it should be created when attaching a file to
        a maintenance request using that equipment.
        """
        # Pre-condition
        folder_id = self.env["documents.folder"].search(
            [
                ("maintenance_equipment_id", "=", self.equipment_01.id),
            ]
        )
        self.assertFalse(folder_id)

        # Arrange
        request_id = self._create_maintenance_request()

        # Act
        folder_id = self.env["documents.folder"].search(
            [
                ("maintenance_equipment_id", "=", self.equipment_01.id),
            ]
        )

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(folder_id)
        self.assertEqual(folder_id.parent_folder_id, self.root_folder_id)

    def test_get_documents_from_maintenance_request(self):
        # Arrange
        request_id = self._create_maintenance_request()

        # Act
        doc_ids = request_id._get_document_ids()

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(doc_ids)
        self.assertEqual(len(doc_ids), 1)

    def test_get_documents_from_maintenance_equipment(self):
        # Arrange
        request_id = self._create_maintenance_request()
        equipment_id = request_id.equipment_id

        # Act
        doc_ids = equipment_id._get_document_ids()

        # Assert
        self._assert_folder_structure(request_id)
        self.assertTrue(doc_ids)
        self.assertEqual(len(doc_ids), 1)
