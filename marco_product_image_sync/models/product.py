from typing import List

import requests
from odoo import Command, api, fields, models

URL = "https://api.marco.it/odoo/images"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_image_sync(self):
        product_ids = self.search([])
        for product in product_ids:
            images: List[str] = requests.get(
                URL, params={"default_code": product.default_code}
            ).json()
            for image in images:
                product.image_1920 = image
                product.product_template_image_ids = [
                    (2, old_img.id, 0) for old_img in product.product_template_image_ids
                ]
                product.product_template_image_ids = [
                    (0, 0, {"image_1920": image, "name": "immagine123"})
                ]
