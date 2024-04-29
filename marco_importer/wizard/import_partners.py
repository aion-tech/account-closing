from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

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
                if not country:
                    raise ValueError(f"Country {rec['Country']} not found:{rec}")

                # cerco la provincia, usando lo stato
                if rec["County"]:
                    domain = [
                        ("code", "=", rec["County"]),
                        ("country_id", "=", country.id),
                    ]
                    state = self.env["res.country.state"].search(domain)
                    if not state:
                        raise ValueError(
                            f"State {rec['County']} - {rec['Country']} not found:{rec}"
                        )
                else:
                    state = False
            else:  
                if rec["ISOCountryCode"]and rec["ISOCountryCode"]!='':
                    domain = [("code", "=", rec["ISOCountryCode"])]
                    country = self.env["res.country"].search(domain)
                    if not country:
                        raise ValueError(f"Country {rec['ISOCountryCode']} not found:{rec}")
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
