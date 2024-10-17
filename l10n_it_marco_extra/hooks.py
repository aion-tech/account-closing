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
    delete_l10n_it_reverse_charge_records(env)
    update_payment_account(env)


def delete_journals(env):
    # Definisce i codici dei journal da eliminare
    codes_to_delete = ["INV", "BILL", "EXCH", "CABA", "CSH1", "BNK1"]

    # Cerca i journal che hanno uno dei codici specificati
    journals_to_delete = env["account.journal"].search([("code", "in", codes_to_delete)])

    # Log del tentativo di archiviazione
    for journal in journals_to_delete:
        _logger.info(f"Archiviazione journal: ID={journal.id}, Name={journal.name}, Code={journal.code}")
        new_name = f"{journal.name} | (Default di ODOO)"
        journal.write({"active": False, "name": new_name})


def update_misc_journal(env):
    # Cerca il journal con il codice 'MISC'
    misc = env['account.journal'].search([('code', '=', 'MISC')])
    _logger.info(f"Aggiornamento journal MISC: ID={misc.id}, Name={misc.name}")
    # Aggiorna il codice e il nome del journal 'MISC'
    misc.write({
        "code": "VARIE",     # Nuovo codice per il journal
        "name": "Operazioni Varie"  # Nuovo nome per il journal
    })

def delete_accounts(env):
    # Cerca i conti con i codici che iniziano con '180', '182', '183' o '999'
    accounts_to_delete = env["account.account"].search([
        "|", "|", "|",
        ("code", "=like", "180%"),
        ("code", "=like", "182%"),
        ("code", "=like", "183%"),
        ("code", "=like", "999%"),
    ])

    # Log del tentativo di archiviazione
    for account in accounts_to_delete:
        _logger.info(f"Archiviazione account: ID={account.id}, Code={account.code}, Name={account.name}")
        new_name = f"{account.name} | (Default di ODOO)"
        account.write({"deprecated": True, "name": new_name})


def archive_payment_terms(env):
    # Cerca tutti gli XML ID che iniziano con 'account_payment_term_' nel modulo 'account'
    xml_id_prefix = "account_payment_term_"
    ir_model_data = env["ir.model.data"].search([
        ("module", "=", "account"),
        ("model", "=", "account.payment.term"),
        ("name", "like", xml_id_prefix + "%"),
    ])
    
    for record in ir_model_data:
        try:
            # Ottieni il termine di pagamento usando il riferimento XML ID
            payment_term = env.ref(f"{record.module}.{record.name}")
            _logger.info(f"Archiviazione termine di pagamento: ID={payment_term.id}, Name={payment_term.name}")
            new_name = f"{payment_term.name} | (Default di ODOO)"
            payment_term.write({"active": False, "name": new_name})
        except ValueError:
            # Gestisci l'errore se l'XML ID non esiste
            _logger.error(f"Errore nel trovare il termine di pagamento per XML ID={record.name}")


def delete_l10n_it_reverse_charge_records(env):
    # Identifica solo i record nel modello 'account.rc.type' creati dal modulo 'l10n_it_reverse_charge'
    ir_model_data_records = env["ir.model.data"].search([
        ("module", "=", "l10n_it_reverse_charge"),
        ("model", "=", "account.rc.type")
    ])
    
    # Per ogni record trovato, registra il tentativo di eliminazione
    for record in ir_model_data_records:
        model = record.model
        res_id = record.res_id
        try:
            record_to_delete = env[model].browse(res_id)
            _logger.info(f"Eliminazione record: Model={model}, Res ID={res_id}, Name={record_to_delete.name}")
            
            # Elimina il record
            record_to_delete.unlink()
        except Exception as e:
            _logger.error(f"Errore durante l'eliminazione del record {res_id} nel modello {model}: {e}")
    
    # Elimina anche le voci in ir.model.data per evitare riferimenti orfani
    _logger.info(f"Eliminazione record ir.model.data per il modulo l10n_it_reverse_charge")
    ir_model_data_records.unlink()


def update_payment_account(env):
    # Cerca i journals di tipo 'bank' e 'cash'
    journals = env["account.journal"].search([("type", "in", ["bank", "cash"])])
    
    # Riferimenti agli account di pagamenti e ricevute in sospeso
    outstanding_payments_account_ref = env.ref("l10n_it_marco.1_22SUPAGA")
    outstanding_receipts_account_ref = env.ref("l10n_it_marco.1_22SURICE")
    
    for journal in journals:
        _logger.info(f"Aggiornamento journal: ID={journal.id}, Nome={journal.name}, Tipo={journal.type}")

        # Aggiornamento per ricevute in sospeso
        inbound_payment_lines = journal.inbound_payment_method_line_ids
        for payment_line in inbound_payment_lines:
            _logger.info(
                f"Ricevute in sospeso - Metodo: {payment_line.payment_method_id.name}, "
                f"Nuovo Account: {outstanding_receipts_account_ref.id}"
            )
            payment_line.payment_account_id = outstanding_receipts_account_ref

        # Aggiornamento per pagamenti in sospeso
        outbound_payment_lines = journal.outbound_payment_method_line_ids
        for payment_line in outbound_payment_lines:
            _logger.info(
                f"Pagamenti in sospeso - Metodo: {payment_line.payment_method_id.name}, "
                f"Nuovo Account: {outstanding_payments_account_ref.id}"
            )
            payment_line.payment_account_id = outstanding_payments_account_ref
