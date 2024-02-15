import time

from odoo.tests.common import TransactionCase, tagged

from .common import MarcoMaintenanceTestCommon

DATA = "data:application/zip;base64,R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="


@tagged("marco")
class MarcoMaintenanceTest(MarcoMaintenanceTestCommon):
    def setUp(self):
        super().setUp()

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

    def test_get_folder(self):
        # Arrange
        folder_id = self.env["documents.folder"].create(
            {
                "name": self.equipment_01.name,
                "maintenance_equipment_id": self.equipment_01.id,
            }
        )

        # Act
        request_id = self._create_maintenance_request()
        request_folder_id = request_id._get_document_folder()

        # Assert
        self.assertTrue(request_folder_id.id == folder_id.id)

    def test_folder_creation(self):
        # Arrange
        folder_id = self.env["documents.folder"].search(
            [
                ("maintenance_equipment_id", "=", self.equipment_01.id),
            ]
        )

        # Pre-condition
        self.assertFalse(folder_id)

        # Act
        self._create_maintenance_request()
        folder_id = self.env["documents.folder"].search(
            [
                ("maintenance_equipment_id", "=", self.equipment_01.id),
            ]
        )

        # Assert
        self.assertTrue(folder_id)
