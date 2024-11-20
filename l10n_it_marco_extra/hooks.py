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
    update_transitory_bank_journals(env)
    main_company = env.ref("base.main_company")
    bolle_doganali_settings(env, main_company)
    sepa_settings(env,main_company)

def sepa_settings(env, main_company):
    main_company.sepa_initiating_party_name = "MARCO S.p.A."
    main_company.sepa_orgid_id = "IT08ZZZ0000001239410176"
    main_company.sepa_orgid_issr = False
    main_company.sdd_creditor_identifier = "IT08ZZZ0000001239410176"


def bolle_doganali_settings(env, main_company):
    main_company.bill_of_entry_partner_id = env.ref(
        "l10n_it_marco_extra.partner_10FEDOGA"
    )
    main_company.bill_of_entry_journal_id = env.ref(
        "l10n_it_marco_extra.account_journal_DOG"
    )
    main_company.bill_of_entry_tax_id = env.ref("l10n_it_marco.1_tax_22im_purchase")


def delete_journals(env):
    # Definisce i codici dei journal da eliminare
    codes_to_delete = ["INV", "BILL", "EXCH", "CABA", "CSH1", "BNK1"]

    # Cerca i journal che hanno uno dei codici specificati
    journals_to_delete = env["account.journal"].search(
        [("code", "in", codes_to_delete)]
    )

    # Log del tentativo di archiviazione
    for journal in journals_to_delete:
        _logger.info(
            f"Archiviazione journal: ID={journal.id}, Name={journal.name}, Code={journal.code}"
        )
        new_name = f"{journal.name} | (Default di ODOO)"
        journal.write({"active": False, "name": new_name})


def update_misc_journal(env):
    # Cerca il journal con il codice 'MISC'
    misc = env["account.journal"].search([("code", "=", "MISC")])
    _logger.info(f"Aggiornamento journal MISC: ID={misc.id}, Name={misc.name}")
    # Aggiorna il codice e il nome del journal 'MISC'
    misc.write(
        {
            "code": "VARIE",  # Nuovo codice per il journal
            "name": "Operazioni Varie",  # Nuovo nome per il journal
        }
    )


def delete_accounts(env):
    # Cerca i conti con i codici che iniziano con '180', '182', '183' o '999'
    accounts_to_delete = env["account.account"].search(
        [
            "|",
            "|",
            "|",
            ("code", "=like", "180%"),
            ("code", "=like", "182%"),
            ("code", "=like", "183%"),
            ("code", "=like", "999%"),
        ]
    )

    # Log del tentativo di archiviazione
    for account in accounts_to_delete:
        _logger.info(
            f"Archiviazione account: ID={account.id}, Code={account.code}, Name={account.name}"
        )
        new_name = f"{account.name} | (Default di ODOO)"
        account.write({"deprecated": True, "name": new_name})


def archive_payment_terms(env):
    # Cerca tutti gli XML ID che iniziano con 'account_payment_term_' nel modulo 'account'
    xml_id_prefix = "account_payment_term_"
    ir_model_data = env["ir.model.data"].search(
        [
            ("module", "=", "account"),
            ("model", "=", "account.payment.term"),
            ("name", "like", xml_id_prefix + "%"),
        ]
    )

    for record in ir_model_data:
        try:
            # Ottieni il termine di pagamento usando il riferimento XML ID
            payment_term = env.ref(f"{record.module}.{record.name}")
            _logger.info(
                f"Archiviazione termine di pagamento: ID={payment_term.id}, Name={payment_term.name}"
            )
            new_name = f"{payment_term.name} | (Default di ODOO)"
            payment_term.write({"active": False, "name": new_name})
        except ValueError:
            # Gestisci l'errore se l'XML ID non esiste
            _logger.error(
                f"Errore nel trovare il termine di pagamento per XML ID={record.name}"
            )


def delete_l10n_it_reverse_charge_records(env):
    # Identifica solo i record nel modello 'account.rc.type' creati dal modulo 'l10n_it_reverse_charge'
    ir_model_data_records = env["ir.model.data"].search(
        [("module", "=", "l10n_it_reverse_charge"), ("model", "=", "account.rc.type")]
    )

    # Per ogni record trovato, registra il tentativo di eliminazione
    for record in ir_model_data_records:
        model = record.model
        res_id = record.res_id
        try:
            record_to_delete = env[model].browse(res_id)
            _logger.info(
                f"Eliminazione record: Model={model}, Res ID={res_id}, Name={record_to_delete.name}"
            )

            # Elimina il record
            record_to_delete.unlink()
        except Exception as e:
            _logger.error(
                f"Errore durante l'eliminazione del record {res_id} nel modello {model}: {e}"
            )

    # Elimina anche le voci in ir.model.data per evitare riferimenti orfani
    _logger.info(
        f"Eliminazione record ir.model.data per il modulo l10n_it_reverse_charge"
    )
    ir_model_data_records.unlink()


def update_transitory_bank_journals(env):
    # Prova a ottenere il riferimento per l'account transitorio
    try:
        transitory_account_ref = env.ref("l10n_it_marco.1_04TRAUFA")
    except ValueError:
        _logger.error("L'account transitorio 'l10n_it_marco.1_04TRAUFA' non esiste.")
        return  # Esci dalla funzione se l'account non esiste

    _logger.info(f"Account transitorio trovato: {transitory_account_ref.id}")

    # Cerca i journals di tipo 'bank' con default_account_id uguale a transitory_account_ref
    transitory_journals = env["account.journal"].search(
        [("type", "=", "bank"), ("default_account_id", "=", transitory_account_ref.id)]
    )

    _logger.info(
        f"Trovati {len(transitory_journals)} registri con conto transitorio come default."
    )

    for journal in transitory_journals:
        _logger.info(
            f"Aggiornamento journal: ID={journal.id}, Nome={journal.name}, Tipo={journal.type}"
        )

        # Imposta entrambi i conti per pagamenti e ricevute in sospeso all'account transitorio
        outstanding_payments_account_ref = transitory_account_ref
        outstanding_receipts_account_ref = transitory_account_ref

        _logger.info(
            f"Impostato outstanding_payments_account_ref e outstanding_receipts_account_ref su {transitory_account_ref.id}"
        )

        # Funzione per aggiornare le righe di metodo di pagamento o eliminarle se il metodo non è 'Manual'
        def update_or_remove_payment_lines(payment_lines, account_ref, direction):
            for payment_line in payment_lines:
                # Controlla se il metodo di pagamento è 'Manual'
                if payment_line.payment_method_id.code == "manual":
                    _logger.info(
                        f"{direction.capitalize()} - Metodo Manual: {payment_line.payment_method_id.name}, "
                        f"Nuovo Account: {account_ref.id}"
                    )
                    # Aggiorna il payment_account_id
                    payment_line.payment_account_id = account_ref
                else:
                    _logger.info(
                        f"Eliminazione della payment_line per il metodo: {payment_line.payment_method_id.name}"
                    )
                    payment_line.unlink()  # Elimina la payment_line

        # Aggiorna o elimina i conti di pagamento per ricevute e pagamenti
        update_or_remove_payment_lines(
            journal.inbound_payment_method_line_ids,
            outstanding_receipts_account_ref,
            "ricevute in sospeso",
        )
        update_or_remove_payment_lines(
            journal.outbound_payment_method_line_ids,
            outstanding_payments_account_ref,
            "pagamenti in sospeso",
        )
