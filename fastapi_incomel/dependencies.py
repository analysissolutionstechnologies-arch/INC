# # -*- coding:utf-8 -*-
#
# import sys
# from datetime import datetime, timedelta
# import logging
#
# from fastapi import Depends, HTTPException, status
# from fastapi.responses import JSONResponse
#
# import jwt
#
# if sys.version_info >= (3, 9):
#     from typing import Annotated
# else:
#     from typing_extensions import Annotated
#
# from odoo.api import Environment
#
# from .schemas import TokenData
# from contextvars import ContextVar
#
# ALGORITHM = "HS256"
# odoo_env_ctx: ContextVar[Environment] = ContextVar("odoo_env_ctx")
# _logger = logging.getLogger("__name__")
#
#
# credentials_exception = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not generator access token"
# )
#
#
# def odoo_env() -> Environment:
#     env = odoo_env_ctx.get()
#     yield env
#
#
# def get_user(login: str, env: Annotated[Environment, Depends(odoo_env)]):
#     return env["res.users"].sudo().search([("login", "=", login)], limit=1)
#
#
# def authenticate_user(
#     login: str, password: str, env: Annotated[Environment, Depends(odoo_env)]
# ):
#     user = get_user(login, env)
#     if not user:
#         return False
#     if (
#         not env["res.users"]
#         .sudo()
#         .authenticate(env.cr.dbname, user.login, password, {"interactive": True})
#     ):
#         return False
#
#     user.write({"last_signin_at": datetime.utcnow()})
#
#     return user
#
#
# def get_param_token(env):
#     param = env["res.config.settings"].sudo().get_param_token()
#     if not param.get("secret_token") or not param.get("refresh_secret_token"):
#         raise credentials_exception
#
#     return param
#
#
# def create_token(data: dict, env: Annotated[Environment, Depends(odoo_env)]):
#     param = get_param_token(env)
#     to_encode_access = data.copy()
#     to_encode_refresh = data.copy()
#     to_encode_access.update(
#         {
#             "exp": data.get("iat", datetime.utcnow())
#             + timedelta(minutes=int(param.get("access_token_expire_mitutes")))
#         }
#     )
#     to_encode_refresh.update(
#         {
#             "exp": data.get("iat", datetime.utcnow())
#             + timedelta(days=int(param.get("refresh_token_expire_days")))
#         }
#     )
#     return {
#         "access_token": jwt.encode(
#             to_encode_access, param.get("secret_token"), algorithm=ALGORITHM
#         ),
#         "refresh_token": jwt.encode(
#             to_encode_refresh, param.get("refresh_secret_token"), algorithm=ALGORITHM
#         ),
#         "expires_in": 60 * int(param.get("access_token_expire_mitutes")),
#         "token_type": "bearer",
#     }
#
#
# def get_access_token(
#     refresh_token: str, env: Annotated[Environment, Depends(odoo_env)]
# ):
#     try:
#         param = get_param_token(env)
#         payload = jwt.decode(
#             refresh_token,
#             param.get("refresh_secret_token"),
#             algorithms=[ALGORITHM],
#         )
#
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(login=username)
#     except jwt.PyJWTError:
#         raise credentials_exception
#
#     user = get_user(login=token_data.login, env=env)
#     if user is None:
#         raise credentials_exception
#
#     now = datetime.utcnow()
#     user.write({"last_signin_at": now})
#     return create_token(data={"sub": user.login, "iat": now}, env=env)
#
#
# def _rollback(reason: str) -> None:
#     cr = odoo_env_ctx.get().cr
#     if cr is not None:
#         _logger.debug("rollback on %s", reason)
#         cr.rollback()
#
# def odoo_exception_handler(status_code, reason, user) -> JSONResponse:
#     _rollback(reason)
#     return JSONResponse(
#         status_code=status_code,
#         content={
#             "success": False,
#             "error": reason,
#             "user": user,
#             "result": None
#         },
#     )

# -*- coding:utf-8 -*-
import sys
import logging
from datetime import datetime, timedelta
from contextvars import ContextVar

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
import jwt
from odoo.api import Environment
from .schemas import TokenData

# Configuración del algoritmo y contexto
ALGORITHM = "HS256"
odoo_env_ctx: ContextVar[Environment] = ContextVar("odoo_env_ctx")
_logger = logging.getLogger(__name__)

# Excepción estándar de credenciales
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not generate access token"
)

def odoo_env() -> Environment:
    """Obtiene el entorno de Odoo del contexto."""
    yield odoo_env_ctx.get()

def get_user(login: str, env: Environment = Depends(odoo_env)):
    """Obtiene un usuario por su login."""
    return env["res.users"].sudo().search([("login", "=", login)], limit=1)

def authenticate_user(login: str, password: str, env: Environment = Depends(odoo_env)):
    """
    Autentica un usuario mediante login y contraseña.
    Actualiza la fecha de último inicio de sesión si la autenticación es exitosa.
    """
    user = get_user(login, env)
    if not user:
        return False

    authenticated = env["res.users"].sudo().authenticate(
        env.cr.dbname, user.login, password, {"interactive": True}
    )
    if not authenticated:
        return False

    user.sudo().write({"last_signin_at": datetime.utcnow()})
    return user

def get_param_token(env: Environment):
    """
    Obtiene los parámetros de configuración para los tokens.
    Lanza una excepción si no se encuentran configurados.
    """
    param = env["res.config.settings"].sudo().get_param_token()
    if not param.get("secret_token") or not param.get("refresh_secret_token"):
        raise credentials_exception
    return param

def create_token(data: dict, env: Environment = Depends(odoo_env)):
    """
    Crea un par de tokens (access y refresh) con sus tiempos de expiración.
    """
    param = get_param_token(env)
    current_time = datetime.utcnow()

    to_encode_access = {
        **data,
        "exp": current_time + timedelta(minutes=int(param.get("access_token_expire_mitutes", 60)))
    }
    to_encode_refresh = {
        **data,
        "exp": current_time + timedelta(days=int(param.get("refresh_token_expire_days", 7)))
    }

    return {
        "access_token": jwt.encode(to_encode_access, param.get("secret_token"), algorithm=ALGORITHM),
        "refresh_token": jwt.encode(to_encode_refresh, param.get("refresh_secret_token"), algorithm=ALGORITHM),
        "expires_in": 60 * int(param.get("access_token_expire_mitutes", 60)),
        "token_type": "bearer",
    }

def get_access_token(refresh_token: str, env: Environment = Depends(odoo_env)):
    """
    Valida un refresh token y genera un nuevo par de tokens.
    """
    try:
        param = get_param_token(env)
        payload = jwt.decode(refresh_token, param.get("refresh_secret_token"), algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user(login=username, env=env)
    if not user:
        raise credentials_exception

    now = datetime.utcnow()
    user.sudo().write({"last_signin_at": now})
    return create_token(data={"sub": user.login, "iat": now}, env=env)

def _rollback(reason: str) -> None:
    """
    Realiza un rollback en la base de datos si ocurre un error.
    """
    cr = odoo_env_ctx.get().cr
    if cr:
        _logger.debug("Rollback triggered due to: %s", reason)
        cr.rollback()

def odoo_exception_handler(status_code: int, reason: str, user: dict) -> JSONResponse:
    """
    Maneja excepciones lanzadas en la API y realiza rollback.
    """
    _rollback(reason)
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": reason,
            "user": user,
            "result": None,
        },
    )
