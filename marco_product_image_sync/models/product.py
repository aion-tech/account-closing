from typing import List

import requests
from odoo import Command, api, fields, models, Command
import logging
_logger=logging.getLogger(__name__)
URL = "https://api.marco.it/odoo/images"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_image_sync(self):
        product_ids = self.search([],order="default_code desc")
        for idx,product in enumerate(product_ids):
            params={"default_code": product.default_code}
            if product.sale_ok:
                params["tipo"]=product.categ_id.name
            res: List[str] = requests.get(
                URL, params=params
            )
            _logger.error(f'{product.default_code},{res.status_code}')
            if res.status_code==404:
                continue
            images=res.json()
            for image in images:
                #__import__('pdb').set_trace()
                if image["name"]=="Primary":
                    product.image_1920 = image["image"]
                #[{"image":"image1","name":"primary"}]
                    
                existingImage=product.product_template_image_ids.filtered(lambda img: img.name==image["name"])
                if existingImage:
                    if image["image"]!=existingImage.image_1920:
                        existingImage.write({
                            "image_1920":image["image"]
                            })
                else:
                    existingImage.create({
                        "name":image["name"],
                        "image_1920":image["image"]
                    })
            _logger.warning(f"<--- {str(idx+1)} | {str(len(product_ids))} ---> {product.name}")

            """  
                product.product_template_image_ids = [
                    (2, old_img.id, 0) for old_img in product.product_template_image_ids
                ]
               
                product.product_template_image_ids = [
                    (0, 0, {"image_1920": image, "name": "immagine123"})
                ] 
            """
