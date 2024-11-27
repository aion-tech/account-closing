from odoo import api, SUPERUSER_ID, modules
import logging
import base64

_logger = logging.getLogger(__name__)


def marco_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    settings_to_enable = {
        "group_uom": "Unità di misura",
        "group_product_variant": "Varianti prodotto",
        "group_stock_multi_locations": "Gestione multi-location",
        "group_stock_adv_location": "Gestione avanzata delle location",
        "group_mrp_routings": "Cicli di lavoro",
        "group_mrp_workorder_dependencies": "Dipendenze tra ordini di lavoro",
        "group_unlocked_by_default": "Sbloccato di default",
    }
    
    for group_key, group_name in settings_to_enable.items():
        # Usa il modello di configurazione per controllare e impostare i parametri
        config = env["res.config.settings"].new({group_key: True})
        if not getattr(config, group_key, False):  # Controlla se già attivo
            _logger.info(f"Attivazione del gruppo: {group_name} ({group_key})")
            config.execute()
        else:
            _logger.info(f"Il gruppo {group_name} ({group_key}) è già attivo.")

    # Aggiorna l'accuratezza decimale a 5
    update_decimal_precision(env)

    # Aggiorna il campo rounding delle UoM
    update_uom_rounding(env)

    
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
    
def update_uom_rounding(env):
    """
    Aggiorna il campo rounding delle UoM in base al valore dei digits di `product.decimal_product_uom`,
    escludendo le unità di misura della categoria con ref `uom.uom_categ_wtime`.
    """
    # Ottieni il record `product.decimal_product_uom`
    decimal_product_uom = env.ref("product.decimal_product_uom", raise_if_not_found=False)

    # Controlla che il record esista
    if decimal_product_uom:
        # Calcola il valore di rounding basato sui digits
        digits = decimal_product_uom.digits
        new_rounding = 10 ** -digits if digits > 0 else 1.0

        # Ottieni la categoria `uom.uom_categ_wtime` da escludere
        excluded_category = env.ref("uom.uom_categ_wtime", raise_if_not_found=False)

        # Cerca tutte le unità di misura non appartenenti alla categoria esclusa
        uoms_to_update = env["uom.uom"].search([
            ("category_id", "!=", excluded_category.id)  # Escludi la categoria specifica
        ])

        # Aggiorna il campo rounding per le UoM da aggiornare
        for uom in uoms_to_update:
            _logger.info(
                f"Aggiornamento rounding per UoM: ID={uom.id}, Nome={uom.name}, "
                f"Vecchio Rounding={uom.rounding}, Nuovo Rounding={new_rounding}"
            )
            uom.rounding = new_rounding

        # Log finale
        _logger.info(
            f"Aggiornato il campo rounding per {len(uoms_to_update)} unità di misura a {new_rounding}, "
            f"escludendo la categoria `{excluded_category.name}`."
        )
    else:
        _logger.info("Il record `product.decimal_product_uom` non esiste, nessun aggiornamento effettuato.")
