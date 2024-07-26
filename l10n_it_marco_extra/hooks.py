from odoo import api, SUPERUSER_ID, modules
import logging
import base64

_logger = logging.getLogger(__name__)


def marco_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    delete_journals(env)
    update_misc_journal(env)
    delete_accounts(env)
    archive_payment_terms(env)

def delete_journals(env):
    # Definisce i codici dei journal da eliminare
    codes_to_delete = ['INV', 'BILL', 'EXCH', 'CABA', 'CSH1', 'BNK1']
    
    # Cerca i journal che hanno uno dei codici specificati
    journals_to_delete = env['account.journal'].search([('code', 'in', codes_to_delete)])
    
    # Elimina i journal trovati
    journals_to_delete.unlink()

def update_misc_journal(env):
    # Cerca il journal con il codice 'MISC'
    misc = env['account.journal'].search([('code', '=', 'MISC')])
    
    # Aggiorna il codice e il nome del journal 'MISC'
    misc.write({
        "code": "VARIE",     # Nuovo codice per il journal
        "name": "Operazioni Varie"  # Nuovo nome per il journal
    })

def delete_accounts(env):
    # Cerca i conti con i codici che iniziano con '180', '182', '183' o '999'
    accounts_to_delete = env['account.account'].search([
        '|', '|', '|',
        ('code', '=like', '180%'),
        ('code', '=like', '182%'),
        ('code', '=like', '183%'),
        ('code', '=like', '999%')
    ])
    
    # Elimina i conti trovati
    accounts_to_delete.unlink()


def archive_payment_terms(env):
    # Cerca tutti gli XML ID che iniziano con 'account_payment_term_' nel modulo 'account'
    xml_id_prefix = 'account_payment_term_'
    ir_model_data = env['ir.model.data'].search([('module', '=', 'account'),('model', '=', 'account.payment.term'), ('name', 'like', xml_id_prefix + '%')])
    __import__('pdb').set_trace()
    for record in ir_model_data:
        try:
            # Ottieni il termine di pagamento usando il riferimento XML ID
            payment_term = env.ref(f"{record.module}.{record.name}")
            # Archivia il termine di pagamento impostando 'active' su False
            payment_term.write({'active': False})
            # Modifica il nome del termine di pagamento archiviato
            new_name = f"{payment_term.name} | (Default di ODOO)"
            payment_term.write({'name': new_name})
        except ValueError:
            # Gestisci l'errore se l'XML ID non esiste
            pass
