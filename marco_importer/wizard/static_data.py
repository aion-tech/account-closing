BASE_URL = "https://api.marco.it/odoo/"

import_method_map = {
    "partner": {"method": "import_partners", "slug": "partner"},
    "items": {"method": "import_items", "slug": "items"},
    "bomHead": {"method": "import_bom_heads", "slug": "bom/head"},
    "bomComponent": {"method": "import_bom_components", "slug": "bom/component"},
    "workcenter": {"method": "import_workcenters", "slug": "bom/workcenter"},
    "bomOperation": {"method": "import_bom_operations", "slug": "bom/operation"},
    "supplierPricelist": {"method": "import_supplier_pricelist", "slug": "supplier/pricelist"},
    "ordersHead": {"method": "import_orders_head", "slug": "order/head"},
    "ordersLine": {"method": "import_orders_line", "slug": "order/line"},
}