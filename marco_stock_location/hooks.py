from odoo import api, SUPERUSER_ID, modules
import logging
import base64

_logger = logging.getLogger(__name__)


def marco_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["res.config.settings"].new({"group_stock_multi_locations":True}).execute()
    
    config = env['res.config.settings'].create({})
    # Imposta il valore di barcode_nomenclature_id
    config.barcode_nomenclature_id = env.ref('marco_stock_location.marco_gs1_nomenclature')
    config.execute()