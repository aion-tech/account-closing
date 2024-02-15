import time

from odoo.addons.base.tests.common import TransactionCase
from odoo.addons.maintenance.tests.test_maintenance import TestEquipment


class MarcoMaintenanceTestCommon(TestEquipment):
    def setUp(self):
        super().setUp()
        self.equipment_01 = self.equipment.with_user(self.manager).create(
            {
                "name": 'Samsung Monitor "15',
                "category_id": self.equipment_monitor.id,
                "technician_user_id": self.ref("base.user_root"),
                "owner_user_id": self.user.id,
                "assign_date": time.strftime("%Y-%m-%d"),
                "serial_no": "MT/128/18291016",
                "model": "NP355E5X",
                "color": 3,
            }
        )
