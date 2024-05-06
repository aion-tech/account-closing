from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    employees = fields.Boolean()

    def import_employees(self, records):
        employee_partner_id
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
