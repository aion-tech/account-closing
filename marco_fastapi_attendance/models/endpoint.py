from ast import literal_eval
from typing import List

from fastapi.middleware.cors import CORSMiddleware
from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..routers.marco import marco_api_router

APP_NAME = "marco"


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[
            (APP_NAME, "Marco Endpoint"),
        ],
        ondelete={
            APP_NAME: "cascade",
        },
    )

    def _get_fastapi_routers(self):
        if self.app == APP_NAME:
            return [marco_api_router]
        return super()._get_fastapi_routers()

    def _get_app(self):
        app = super()._get_app()
        return app
