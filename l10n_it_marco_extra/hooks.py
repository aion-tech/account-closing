from odoo import api, SUPERUSER_ID, modules
import logging
import base64

_logger = logging.getLogger(__name__)


def marco_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    delete_journals(env)
    update_misc_journal(env)
    delete_accounts(env)


def delete_journals(env):
    # Definisce i codici dei journal da eliminare
    codes_to_delete = ['INV', 'BILL', 'EXCH', 'CABA', 'CSH1', 'BNK1']
    
    # Cerca i journal che hanno uno dei codici specificati
    journals = env['account.journal'].search([('code', 'in', codes_to_delete)])
    
    # Elimina i journal trovati
    journals.unlink()

def update_misc_journal(env):
    # Cerca il journal con il codice 'MISC'
    misc = env['account.journal'].search([('code', '=', 'MISC')])
    
    # Aggiorna il codice e il nome del journal 'MISC'
    misc.write({
        "code": "VARIE",     # Nuovo codice per il journal
        "name": "Operazioni Varie"  # Nuovo nome per il journal
    })

def delete_accounts(env):
   # Cerca e elimina i conti con i codici che iniziano con '180', '182', '183' o '999'
    accounts_to_delete = env['account.account'].search([
        '|', '|', '|',
        ('code', '=like', '180%'),
        ('code', '=like', '182%'),
        ('code', '=like', '183%'),
        ('code', '=like', '999%')
    ])
    
    # Elimina i conti trovati
    accounts_to_delete.unlink()

