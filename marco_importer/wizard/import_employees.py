from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    employees = fields.Boolean()

    def import_employees(self, records):
        
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
        employee_partner_id = self.env["res.partner"].search([("ref", "=", rec[""])])
        if employee_partner_id:

            employee_partner_id.with_context(no_vat_validation=True).write(
                vals
            )  # per ora ignoro tutti i check sul VAT no
        else:
            employee_partner_id = (
                self.env["res.partner"]
                .with_context(no_vat_validation=True)
                .create(vals)
            )  # per ora ignoro tutti i check sul VAT no

        _logger.warning("<--- IMPORTAZIONE EMPLOYEES INIZIATA --->")
        for idx, rec in enumerate(records):
            
            vals = {
                "bic": rec["bic"],
                "abi": rec["abi"],
                "cab": rec["cab"],
                #"email": rec["email"],
                "name": rec["name"],
                "phone": rec["phone"],
                "city" : rec["city"],
                "street": rec["street"],
                "zip": rec["zip"],
                "banca_estera": rec["banca_estera"],
                "country": country and country.id,
                "state": state and state.id,
            }
            employee_id = self.env["res.bank"].search(
                [("bic", "=", rec["bic"]),("abi", "=", rec["abi"]),("cab", "=", rec["cab"])]
            )
            if employee_id:
                employee_id.write(vals)
            else:
                employee_id = self.env["res.bank"].create(vals)
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=employee_id and employee_id.name,
            )
        _logger.warning("<--- IMPORTAZIONE BANCHE TERMINATA --->")
