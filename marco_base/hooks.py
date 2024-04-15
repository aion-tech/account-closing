from odoo import api, SUPERUSER_ID

def marco_post_init_hook(cr,registry):
    env=api.Environment(cr,SUPERUSER_ID,{})
    env["res.config.settings"].new({"group_uom": True}).execute()
    env["res.config.settings"].new({ "group_product_variant": True}).execute()
    env["res.config.settings"].new({ "group_stock_multi_locations": True}).execute()
    env["res.config.settings"].new({ "group_stock_adv_location": True}).execute()
    env["res.config.settings"].new({"group_mrp_routings":True}).execute()
    env["res.config.settings"].new({"module_mrp_workorder":True}).execute()
    env["res.config.settings"].new({ "module_mrp_subcontracting":True}).execute()
