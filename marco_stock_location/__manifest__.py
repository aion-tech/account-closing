# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "MARCO LOCATION",
    "version": "0.1",
    "depends": [
        "stock",
        "stock_barcode",
        "web_notify",
        "queue_job",
        "stock_location_position",
    ],
    "author": "MARCO S.p.A.",
    "description": """
Gestione dello stock custom MARCO S.p.A. .
================================================

Italian accounting chart and localization.
    """,
    "category": "Uncategorize",
    "website": "http://www.marco.it/",
    "data": [
        "views/stock_location_views.xml",
        "data/wms_location.xml",
        "data/wms_location_CLAV.xml",
        "data/actions.xml",
        "data/wms_locations/macro_areas.xml",
        "data/wms_locations/wms_location_M3_A1.xml",
        "data/wms_locations/wms_location_M3_A2.xml",
        "data/wms_locations/wms_location_M3_A3.xml",
        "data/wms_locations/wms_location_M3_A4.xml",
        "data/wms_locations/wms_location_M3_A5.xml",
        "data/wms_locations/wms_location_M3_A6.xml",
        "data/wms_locations/wms_location_M3_A7.xml",
        "data/wms_locations/wms_location_M2_A2.xml",
        "data/wms_locations/wms_location_M2_A3.xml",
        "data/wms_locations/wms_location_M2_A4.xml",
        "data/wms_locations/wms_location_M2_A5.xml",
        "data/wms_locations/wms_location_M2_A6.xml",
        "data/wms_locations/wms_location_M2_A7.xml",
        "data/wms_locations/wms_location_M2_A1.xml",
        "data/wms_locations/wms_location_M1_A1.xml",
        "data/wms_locations/wms_location_M1_A2.xml",
        "data/wms_locations/wms_location_M1_A3.xml",
        "data/wms_locations/wms_location_M1_A6.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "marco_stock_location/static/src/**/*.js",
        ]
    },
    "post_init_hook": "marco_post_init_hook",
    "license": "LGPL-3",
}
