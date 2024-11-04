from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger


STANDARD_ADDRESSEE_CODE = "0000000"

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"

    partners = fields.Boolean(string="Partners")

    def import_partners(self, records):
        _logger.warning("<--- IMPORTAZIONE PARTNERS INIZIATA --->")
        for idx, rec in enumerate(records):
            # cerco lo stato partendo dall'ISO Code se non esiste fermo tutto
            if rec["Country"] and rec["Country"]!='':
                domain = [("code", "=", rec["Country"])]
                country = self.env["res.country"].search(domain)
               

                # cerco la provincia, usando lo stato
                if rec["County"]:
                    domain = [
                        ("code", "=", rec["County"]),
                        ("country_id", "=", country.id),
                    ]
                    state = self.env["res.country.state"].search(domain)
                    
                else:
                    state = False
            else:  
                if rec["ISOCountryCode"]and rec["ISOCountryCode"]!='':
                    domain = [("code", "=", rec["ISOCountryCode"])]
                    country = self.env["res.country"].search(domain)
                    
                else:
                    country = False
                state = False

            # instanzio category come array vuoto
            category = []
            # cerco il settore nelle categorie dei partners e la creo se non esiste
            if rec["settore"]:
                domain = [("name", "=", rec["settore"])]
                settore = self.env["res.partner.category"].search(domain)
                if not settore:
                    settore = self.env["res.partner.category"].create(
                        {"name": rec["settore"]}
                    )
                category.append(settore.id)
            # cerco la tipolgia nelle categorie dei partners e la creo se non esiste
            if rec["tipologia"]:
                domain = [("name", "=", rec["tipologia"])]
                tipologia = self.env["res.partner.category"].search(domain)
                if not tipologia:
                    tipologia = self.env["res.partner.category"].create(
                        {"name": rec["tipologia"]}
                    )
                category.append(tipologia.id)

            if not category:
                category = False

            vals = {
                "name": rec["CompanyName"],
                "ref": rec["CustSupp"],
                "vat": rec["TaxIdNumber"],
                "fiscalcode":rec["FiscalCode"],
                "street": rec["Address"],
                "zip": rec["ZIPCode"],
                "city": rec["City"],
                "phone": rec["Telephone1"],
                "website": rec["Internet"],
                # "email": rec["EMail"],
                "is_company": rec["isCompany"],
                "vat": rec["TaxIdNumber"],
                "country_id": country and country.id,
                "state_id": state and state.id,
                "category_id": category and [Command.set(category)],
                "is_pa":rec["is_pa"]== "1",
                "electronic_invoice_subjected":rec["electronic_invoice_subjected"]== "1",
                "electronic_invoice_obliged_subject":rec["electronic_invoice_subjected"]== "1",
                "eori_code":rec["eori_code"],
                "codice_destinatario":rec["is_pa"]!= "1" and rec["codice_destinatario"],
                "ipa_code":rec["is_pa"]== "1" and rec["codice_destinatario"],

            }
            # Controlla i requisiti di fatturazione elettronica e ottiene i messaggi di errore
            error_reasons = self.check_partner_einvoice_requirements(vals)

            partner_id = self.env["res.partner"].search([("ref", "=", rec["CustSupp"])])
            if partner_id:

                partner_id.with_context(no_vat_validation=True).write(
                    vals
                )  # per ora ignoro tutti i check sul VAT no
            else:
                partner_id = (
                    self.env["res.partner"]
                    .with_context(no_vat_validation=True)
                    .create(vals)
                )  # per ora ignoro tutti i check sul VAT no

            partner_id.email = False
            
            # Aggiungi messaggio di errore nel Chatter se ci sono errori
            if error_reasons:
                # Crea il messaggio HTML formattato con un elenco puntato
                message = (
                    "<b>Errore nei requisiti di fatturazione elettronica:</b><ul>" +
                    "".join([f"<li>{error}</li>" for error in error_reasons]) +
                    "</ul>"
                )
                partner_id.message_post(body=message, subtype_id=self.env.ref('mail.mt_note').id)


            vat_error_message = "P.IVA ERRATA"
            vat_checker = (vat_error_message, False)[
                partner_id.simple_vat_check(
                    country_code=rec["ISOCountryCode"],
                    vat_number=rec["TaxIdNumber"],
                )
            ]
            if vat_checker and rec["TaxIdNumber"] != "":
                vat_checker_tag = self.env["res.partner.category"].search(
                    [("name", "=", vat_checker)]
                )
                if not vat_checker_tag:
                    vat_checker_tag = self.env["res.partner.category"].create(
                        {"name": vat_checker}
                    )

                partner_id.category_id = [Command.link(vat_checker_tag.id)]

            else:
                vat_was_wrong = partner_id.category_id.search(
                    [("name", "=", vat_error_message)]
                )
                if vat_error_message:
                    command = Command.unlink(vat_was_wrong.id)

            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=vat_checker,  # partner_id and partner_id.name,
            )

        _logger.warning("<--- IMPORTAZIONE PARTNERS TERMINATA --->")
        # self.env.cr.commit()

    def check_partner_einvoice_requirements(self, vals):
        """
        Verifica i requisiti di fatturazione elettronica per un partner nei dati vals.
        Se una delle condizioni non è soddisfatta, imposta 'electronic_invoice_subjected' 
        e 'electronic_invoice_obliged_subject' a False in vals e aggiunge il tag 'Errore FE'.
        Restituisce una lista di messaggi di errore in italiano.
        """
        valid = True
        fe_error_message = "Errore FE"
        error_reasons = []  # Lista per memorizzare tutte le ragioni dell'errore

        # Determina se il partner è italiano basandosi su `country_id`
        italian_country_id = self.env["res.country"].search([("code", "=", "IT")], limit=1).id

        if vals.get("electronic_invoice_subjected"):
            if vals.get("is_pa") and (not vals.get("ipa_code") or len(vals["ipa_code"]) != 6):
                valid = False
                error_reasons.append("Codice IPA mancante o di lunghezza errata per PA")

            if (
                vals.get("is_company") == "person"
                and not vals.get("company_name")
                and (not vals.get("lastname") or not vals.get("firstname"))
            ):
                valid = False
                error_reasons.append("Nome azienda o nome e cognome mancanti per persona fisica")

            if not vals.get("is_pa") and not vals.get("codice_destinatario"):
                valid = False
                error_reasons.append("Codice destinatario mancante per non PA")

            if not vals.get("is_pa") and vals.get("codice_destinatario") and len(vals["codice_destinatario"]) != 7:
                valid = False
                error_reasons.append("Codice destinatario di lunghezza errata per non PA")

            if vals.get("pec_destinatario") and vals.get("codice_destinatario") != STANDARD_ADDRESSEE_CODE:
                valid = False
                error_reasons.append("PEC destinatario presente con codice destinatario errato")

            # Verifica se il partner è italiano usando `italian_country_id`
            if not vals.get("vat") and not vals.get("fiscalcode") and vals.get("country_id") == italian_country_id:
                valid = False
                error_reasons.append("Partita IVA e codice fiscale mancanti per partner italiano")

            if not vals.get("street"):
                valid = False
                error_reasons.append("Indirizzo mancante")

            if not vals.get("zip") and vals.get("country_id") == italian_country_id:
                valid = False
                error_reasons.append("CAP mancante per partner italiano")

            if not vals.get("city"):
                valid = False
                error_reasons.append("Città mancante")

            if not vals.get("country_id"):
                valid = False
                error_reasons.append("Nazione mancante")

        if not valid:
            # Imposta i campi su False se i requisiti non sono soddisfatti
            vals["electronic_invoice_subjected"] = False
            vals["electronic_invoice_obliged_subject"] = False

            # Cerca o crea il tag "Errore FE"
            fe_error_tag = self.env["res.partner.category"].search([("name", "=", fe_error_message)])
            if not fe_error_tag:
                fe_error_tag = self.env["res.partner.category"].create({"name": fe_error_message})

            # Aggiunge il tag "Errore FE" al campo category_id
            if "category_id" in vals and vals["category_id"]:
                # Aggiunge il tag "Errore FE" alla lista esistente
                vals["category_id"].append(Command.link(fe_error_tag.id))
            else:
                # Crea una nuova lista con il tag "Errore FE"
                vals["category_id"] = [Command.link(fe_error_tag.id)]
        
        # Restituisce i messaggi di errore per l'inserimento nel Chatter
        return error_reasons

