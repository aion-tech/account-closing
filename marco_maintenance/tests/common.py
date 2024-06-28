import time

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT, TransactionCase


class MarcoMaintenanceTestCommon(TransactionCase):
    def setUp(self):
        super().setUp()

        self.equipment = self.env["maintenance.equipment"]
        self.maintenance_request = self.env["maintenance.request"]
        self.res_users = self.env["res.users"].with_context(DISABLED_MAIL_CONTEXT)
        self.maintenance_team = self.env["maintenance.team"]
        self.main_company = self.env.ref("base.main_company")
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
