import time

from odoo.addons.base.tests.common import (DISABLED_MAIL_CONTEXT,
                                           TransactionCase)


class MarcoMaintenanceTestCommon(TransactionCase):
    def setUp(self):
        super().setUp()

        self.root_folder_id = self.env.ref(
            "marco_maintenance.documents_maintenance_folder"
        )
        self.equipment = self.env["maintenance.equipment"]
        self.maintenance_request = self.env["maintenance.request"]
        self.res_users = self.env["res.users"].with_context(DISABLED_MAIL_CONTEXT)
        self.maintenance_team = self.env["maintenance.team"]
        self.main_company = self.env.ref("base.main_company")
        self.data = "data:application/zip;base64,R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="
        res_user = self.env.ref("base.group_user")
        res_manager = self.env.ref("maintenance.group_equipment_manager")

        self.user = self.res_users.create(
            dict(
                name="Normal User/Employee",
                company_id=self.main_company.id,
                login="emp",
                email="empuser@yourcompany.example.com",
                groups_id=[(6, 0, [res_user.id])],
            )
        )

        self.manager = self.res_users.create(
            dict(
                name="Equipment Manager",
                company_id=self.main_company.id,
                login="hm",
                email="eqmanager@yourcompany.example.com",
                groups_id=[(6, 0, [res_manager.id])],
            )
        )

        self.category_01 = self.env["maintenance.equipment.category"].create(
            {"name": "Monitors - Test"}
        )

        self.category_02 = self.env["maintenance.equipment.category"].create(
            {"name": "Manometri - Test"}
        )

        self.equipment_01 = self.equipment.with_user(self.manager).create(
            {
                "name": 'Samsung Monitor "15',
                "category_id": self.category_01.id,
                "technician_user_id": self.ref("base.user_root"),
                "owner_user_id": self.user.id,
                "assign_date": time.strftime("%Y-%m-%d"),
                "serial_no": "MT/128/18291016",
                "model": "NP355E5X",
                "color": 3,
                "maintenance_team_id": self.env["maintenance.team"]
                .search([], limit=1)
                .id,
            }
        )

        self.equipment_02 = self.equipment.with_user(self.manager).create(
            {
                "name": 'HP Monitor "22',
                "category_id": self.category_01.id,
                "technician_user_id": self.ref("base.user_root"),
                "owner_user_id": self.user.id,
                "assign_date": time.strftime("%Y-%m-%d"),
                "serial_no": "HP/3121/1",
                "model": "AAAAAABBBBZZZZ",
                "color": 2,
            }
        )

    def _attach_file_to_category(self, category):
        category_attachment = self.env["ir.attachment"].create(
            {
                "datas": self.data,
                "name": "CategoryAttachment",
                "res_model": "maintenance.equipment.category",
                "res_id": category.id,
            }
        )
        return category_attachment

    def _attach_file_to_equipment(self, equipment):
        equipment_attachment = self.env["ir.attachment"].create(
            {
                "datas": self.data,
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
                "datas": self.data,
                "name": "DataDataData",
                "res_model": "maintenance.request",
                "res_id": request.id,
            }
        )
        return attachment

    def _create_maintenance_request(
        self,
        equipment_id: int,
        category_id: int,
    ):
        request_id = self.maintenance_request.with_user(self.user).create(
            {
                "name": "Resolution is bad",
                "user_id": self.user.id,
                "owner_user_id": self.user.id,
                "equipment_id": equipment_id,
                "color": 7,
                "stage_id": self.ref("maintenance.stage_0"),
                "maintenance_team_id": self.ref(
                    "maintenance.equipment_team_maintenance"
                ),
                "category_id": category_id,
            }
        )
        return request_id

    def _assert_folder_structure(self, request_id):
        request_folder = request_id._get_document_folder()
        self.assertTrue(request_folder)

        # assert parent folders
        equipment_folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", request_id.equipment_id.id),
                ("res_model", "=", "maintenance.equipment"),
            ]
        )
        self.assertTrue(equipment_folder)
        self.assertEqual(
            request_folder.parent_folder_id,
            equipment_folder,
        )

        category_folder = self.env["documents.folder"].search(
            [
                ("res_id", "=", request_id.equipment_id.category_id.id),
                ("res_model", "=", "maintenance.equipment.category"),
            ]
        )
        self.assertTrue(category_folder)
        self.assertEqual(
            equipment_folder.parent_folder_id,
            category_folder,
        )

        # assert res_id/res_model
        self.assertEqual(
            request_folder.res_id,
            request_id.id,
        )
        self.assertEqual(
            request_folder.res_model,
            "maintenance.request",
        )

        self.assertEqual(
            equipment_folder.res_id,
            request_id.equipment_id.id,
        )
        self.assertEqual(
            equipment_folder.res_model,
            "maintenance.equipment",
        )

        self.assertEqual(
            category_folder.res_id,
            request_id.equipment_id.category_id.id,
        )
        self.assertEqual(
            category_folder.res_model,
            "maintenance.equipment.category",
        )
