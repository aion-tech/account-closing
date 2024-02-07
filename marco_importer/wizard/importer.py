from typing import Dict, List

import requests
from odoo import api, fields, models


class MarcoImporter(models.TransientModel):
    _name = "marco.importer"

    url = fields.Char(
        string="URL",
        required=True,
        default="https://api.marco.it/odoo/clients",
    )
    import_type = fields.Selection(
        selection=[("partner", "Partner"), ("bom", "BOM")],
        string="Import Type",
        required=True,
        default="partner",
    )

    def _check_url(self):
        return self.url.startswith("https")

    def import_data(self):
        if not self._check_url():
            raise ValueError("URL must start with 'https'")

        res = requests.get(self.url)
        records = res.json()
        if self.report_type == "partner":
            self.import_partner_data(records)
        if self.report_type == "bom":
            self.import_bom_data(records)

    def import_bom_data(self, records):
        # product = self.env["product.template"].create(
        #     {
        #         "name": "Prodotto Finito",
        #         "detailed_type": "product",
        #     }
        # )
        product = self.env["product.template"].search(
            [("default_code", "=", "PROD0001")]
        )
        if product:
            bom = self.env["mrp.bom"].create(
                {
                    "product_tmpl_id": product.id,
                    "code": "asdfasdf",
                }
            )
            bom_line = self.env["mrp.bom.line"].create({"bom_id": bom.id})

    def import_partner_data(self, records):
        for rec in records[:50]:
            vals = {
                "name": rec["CompanyName"],
                "ref": rec["CustSupp"],
                "vat": rec["FiscalCode"],
                "street": rec["Address"],
                "zip": rec["ZIPCode"],
                "city": rec["City"],
                "phone": rec["Telephone1"],
                "website": rec["Internet"],
                "email": rec["EMail"],
                "is_company": rec["isCompany"],
            }
            domain = [("code", "=", rec["ISOCountryCode"])]
            country = self.env["res.country"].search(domain)

            if not country:
                raise ValueError(f"Country {rec['ISOCountryCode']} not found")

            vals["country_id"] = country.id

            existing_partner = self.env["res.partner"].search(
                [("ref", "=", rec["CustSupp"])]
            )
            if existing_partner:
                existing_partner.write(vals)
            else:
                existing_partner = self.env["res.partner"].create(vals)

            existing_partner.email = False

            print(existing_partner.name)
            self.env.cr.commit()
