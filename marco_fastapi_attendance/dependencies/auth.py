""" from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.security import APIKeyHeader

from odoo import SUPERUSER_ID
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment
from odoo.exceptions import ValidationError


def api_key_auth_user(
    api_key: Annotated[
        str,
        Depends(
            APIKeyHeader(
                name="api-key",
                description="API key",
            )
        ),
    ],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Users:
   
    try:
        api_key_id = (
            
            env["auth.api.key"].with_user(SUPERUSER_ID)._retrieve_api_key(api_key)
        )
        return api_key_id.user_id
    except ValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing api key",
        ) from err
 """
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyQuery

from odoo import SUPERUSER_ID
from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment
from odoo.exceptions import ValidationError

# Dependency to retrieve API key from query parameters
def api_key_auth_user(
    api_key: Annotated[
        str,
        Depends(
            APIKeyQuery(
                name="api-key",
                description="API key",
                auto_error=False  # Set to False to handle error manually
            )
        ),
    ],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Users:
    """
    If the provided API key exists, return the user it belongs to.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    try:
        api_key_id = (
            env["auth.api.key"].with_user(SUPERUSER_ID)._retrieve_api_key(api_key)
        )
        return api_key_id.user_id
    except ValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        ) from err

