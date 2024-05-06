from odoo import api, SUPERUSER_ID, modules
import logging
import base64

_logger = logging.getLogger(__name__)


def marco_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["res.config.settings"].new({"group_uom": True}).execute()
    env["res.config.settings"].new({"group_product_variant": True}).execute()
    env["res.config.settings"].new({"group_stock_multi_locations": True}).execute()
    env["res.config.settings"].new({"group_stock_adv_location": True}).execute()
    env["res.config.settings"].new({"group_mrp_routings": True}).execute()
    env["res.config.settings"].new({"module_mrp_workorder": True}).execute()
    env["res.config.settings"].new({"module_mrp_subcontracting": True}).execute()
    setMarcoAsOdooCompany(env)


def setMarcoAsOdooCompany(env):
    company = env["res.company"].search([])
    print("################# INIZIALIZZAZIONE COMPANY ##################")
    if len(company) != 1:
        raise ValueError(
            f"Sono state impostate più company, non è possibile impostare MARCO come unica company di ODOO"
        )
    elif company.name == "MARCO S.p.A.":
        _logger.warning("<--- MARCO S.p.A. già impostata come company di ODOO --->")
    else:
        domain = [("code", "=", "IT")]
        country = env["res.country"].search(domain)
        if not country:
            raise ValueError(f"Country IT not found: RUN!!!")

        # cerco la provincia, usando lo stato
        domain = [
            ("code", "=", "BS"),
            ("country_id", "=", country.id),
        ]
        state = env["res.country.state"].search(domain)
        if not state:
            raise ValueError(f"State BS not found: RUN!!!")

        favicon_path = modules.module.get_resource_path(
            "marco_base", "static/", "favicon.ico"
        )
        with open(favicon_path, "rb") as f:
            contents = f.read()
        favicon = base64.b64encode(contents)  # convert to base64


        logo_path = modules.module.get_resource_path(
            "marco_base", "static/", "logo.png"
        )
        with open(logo_path, "rb") as f:
            contents = f.read()
        logo = base64.b64encode(contents)  # convert to base64

        vals = {
            "name": "MARCO S.p.A.",
            "street": "Via Mameli 10",
            "city": "Brescia",
            "state_id": state.id,
            "zip": "25082",
            "country_id": country.id,
            "vat": "01239410176",
            "fiscalcode": "01239410176",
            "currency_id": env.ref("base.EUR").id,
            "rea_code": "246134",
            "phone": "03021341",
            "email": "info@marco.it",
            "website": "https://www.marco.it",
            "favicon": favicon,
            "logo": logo,
        }
        company.write(vals)
