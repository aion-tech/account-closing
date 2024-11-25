from odoo import api, SUPERUSER_ID, modules
import logging
import base64

_logger = logging.getLogger(__name__)


def marco_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # con new lo lasci in memoria, con create invece lo crei nel database e viene pulito una volta al giorno  dal crono "auto vacuum ..."
    # vista delle impostazioni per trovare i flag che si voglioni impostare https://github.com/odoo/odoo/blob/16.0/addons/mrp/views/res_config_settings_views.xml
    env["res.config.settings"].new({"group_uom": True}).execute()#unità di misura
    env["res.config.settings"].new({"group_product_variant": True}).execute()#varianti prodotto
    env["res.config.settings"].new({"group_stock_multi_locations": True}).execute()
    env["res.config.settings"].new({"group_stock_adv_location": True}).execute()
    env["res.config.settings"].new({"group_mrp_routings": True}).execute()
    env["res.config.settings"].new({"group_mrp_workorder_dependencies": True,}).execute()
    env["res.config.settings"].new({"group_unlocked_by_default":True}).execute()
    
    # Aggiorna l'accuratezza decimale a 5
    update_decimal_precision(env)

    
def update_decimal_precision(env):
    """
    Aggiorna l'accuratezza decimale a 5 per i record specificati in modo idempotente.
    Non aggiorna i valori di precisione superiori a 5.
    """
    precision_refs = [
        'product.decimal_price',
        'product.decimal_stock_weight',
        'product.decimal_volume',
        'product.decimal_product_uom',
        'account.decimal_payment',
        'l10n_it_fatturapa_out.decimal_unit_price_xmlpa'
    ]
    
    # Recupera gli ID dai riferimenti
    decimal_precision_ids = env['ir.model.data'].search([
        ('model', '=', 'decimal.precision'),
        ('module', '=', 'product')  # Specifica il modulo se necessario
    ]).filtered(lambda r: f"{r.module}.{r.name}" in precision_refs).mapped('res_id')

    if not decimal_precision_ids:
        _logger.info("No decimal precision records found for the given references.")
        return

    # Cerca i record di decimal.precision da aggiornare
    decimal_precisions = env['decimal.precision'].browse(decimal_precision_ids)

    for precision in decimal_precisions:
        if precision.digits < 5:
            _logger.info(f"Updating decimal precision '{precision.name}' from {precision.digits} to 5.")
            precision.digits = 5
        elif precision.digits > 5:
            _logger.info(f"Skipping decimal precision '{precision.name}' with digits={precision.digits}, as it is greater than 5.")
    
