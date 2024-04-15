from odoo import api, fields, models, Command
from .progress_logger import _progress_logger,_logger

class MarcoImporter(models.TransientModel):
    _inherit = "marco.importer"
    partners_bank = fields.Boolean()

    def import_partners_bank(self, records):
        
        _logger.warning("<--- IMPORTAZIONE BANCHE DEI PARTNERS INIZIATA --->")
        for idx, rec in enumerate(records):
            partner_id = self.env["res.partner"].search(
                [("ref", "=", rec["CustSupp"])]
            )
            bank_id = self.env["res.bank"].search(
                [("bic", "=", rec["bic"]),("abi", "=", rec["abi"]),("cab", "=", rec["cab"])]
            )
            if not (partner_id and bank_id):
                continue
            vals = {
               
                "acc_number": rec["acc_number"],
                "allow_out_payment": rec["allow_out_payment"],
                "bank_id": bank_id.id,
                "partner_id":partner_id.id
            }
            partner_bank_id = self.env["res.partner.bank"].search(
                [("bank_id", "=", bank_id.id),("partner_id", "=", partner_id.id),("acc_number", "=", rec["acc_number"])]
            )
            if partner_bank_id:
                partner_bank_id.write(vals)
            else:
                partner_bank_id = self.env["res.partner.bank"].create(vals)
            _progress_logger(
                iterator=idx,
                all_records=records,
                additional_info=partner_bank_id and partner_bank_id.acc_number,
            )
        _logger.warning("<--- IMPORTAZIONE BANCHE DEI PARTNERS TERMINATA --->")
