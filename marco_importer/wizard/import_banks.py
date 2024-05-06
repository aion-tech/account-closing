from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    banks = fields.Boolean()

    def import_banks(self, records):
        
        _logger.warning("<--- IMPORTAZIONE BANCHE INIZIATA --->")
        for idx, rec in enumerate(records):
            if rec["country"]:
                domain = [("code", "=", rec["country"])]
                country = self.env["res.country"].search(domain)
                '''
                if not country:
                    raise ValueError(f"Country {rec['country']} not found:{rec}")
                '''
                # cerco la provincia, usando lo stato
                if rec["county"]:
                    domain = [
                        ("code", "=", rec["county"]),
                        ("country_id", "=", country.id),
                    ]
                    state = self.env["res.country.state"].search(domain)
                    '''if not state:
                        raise ValueError(
                            f"State {rec['county']} - {rec['country']} not found:{rec}"
                        )
                    '''
                else:
                    state = False
            else:
                country = False
                state = False
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
            bank_id = self.env["res.bank"].search(
                [("bic", "=", rec["bic"]),("abi", "=", rec["abi"]),("cab", "=", rec["cab"])]
            )
            if bank_id:
                bank_id.write(vals)
            else:
                bank_id = self.env["res.bank"].create(vals)
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=bank_id and bank_id.name,
            )
        _logger.warning("<--- IMPORTAZIONE BANCHE TERMINATA --->")
