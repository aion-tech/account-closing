from typing import List

import requests
from odoo import Command, api, fields, models, Command
import logging

_logger = logging.getLogger(__name__)
URL = "https://api.marco.it/odoo/images"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_image_sync(self):
        product_ids = self.search(
            [], order="default_code asc"
        )
        for idx, product in enumerate(product_ids):
            params = {"default_code": product.default_code}
            if product.sale_ok:
                params["tipo"] = product.categ_id.name
            res: List[str] = requests.get(URL, params=params)
            if res.status_code != 200:
                _logger.error(
                    f"<--- {str(idx+1)} | {str(len(product_ids))} --->N°of img [0] | {product.default_code} - {product.name}"
                )
                continue
            images = res.json()

            for image in images:
                # __import__('pdb').set_trace()
                if image["name"] == "Primary":
                    product.image_1920 = image["image"]
                    self.env.cr.commit()
                # [{"image":"image1","name":"primary"}]
                elif product.sale_ok:
                    existingImage = product.product_template_image_ids.filtered(
                        lambda img: img.name == image["name"]
                    )

                    if existingImage:
                        if image["image"] != existingImage.image_1920:
                            existingImage.write({"image_1920": image["image"]})
                    else:
                        product.product_template_image_ids = [Command.create({"image_1920": image["image"], "name": image["name"]})]
                    self.env.cr.commit()

            _logger.info(
                f"<--- {str(idx+1)} | {str(len(product_ids))} --->N°of img [{len(images)}] | {product.default_code} - {product.name}"
            )
