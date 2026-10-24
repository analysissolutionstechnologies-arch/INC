# # -*- coding:utf-8 -*-
#
# import base64
# import io
# import re
# import sys
# from datetime import datetime
# from typing import Callable, Optional
#
# if sys.version_info >= (3, 9):
#     from typing import Annotated
# else:
#     from typing_extensions import Annotated
#
# import json
# import time
# from urllib.parse import parse_qsl
#
# import jsonlines
# import jwt
# from fastapi import (BackgroundTasks, Depends, FastAPI, Header, HTTPException,
#                      Request, Response, status)
# from fastapi.responses import RedirectResponse, StreamingResponse
# from fastapi.routing import APIRoute
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from odoo import tools
# from odoo.addons.base.models.res_users import Users
# from odoo.api import Environment, call_kw
# from odoo.exceptions import AccessDenied, MissingError
# from odoo.tools.mimetypes import guess_mimetype
# from odoo.tools.safe_eval import safe_eval
# from starlette.datastructures import MultiDict
# from starlette.types import Message
#
# from .dependencies import (ALGORITHM, authenticate_user, create_token,
#                            get_access_token, get_param_token, get_user,
#                            odoo_env, odoo_exception_handler)
# from .schemas import (ChangePassword, CreateMultiParams, CreateParams,
#                       DeleteParams, MethodParams, OdooModel, ResponseModel,
#                       ResponseModels, Token, TokenData, UpdateParams)
#
# app = FastAPI()
# odoo_routes = []
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 30 * 6
# ############### Define Router V1 ###############
#
# class LogRoute(APIRoute):
#     def get_route_handler(self) -> Callable:
#         original_route_handler = super().get_route_handler()
#
#         async def custom_route_handler(request: Request) -> Response:
#             if not request.url.path in [
#                 "/api/v1/search_read",
#                 "/api/v1/read",
#                 "/api/v1/create",
#                 "/api/v1/multi_create",
#                 "/api/v1/write",
#                 "/api/v1/unlink",
#                 "/api/v1/call_method",
#             ]:
#                 return await original_route_handler(request)
#
#             execution_time = datetime.now().isoformat()
#             start_time = time.perf_counter()
#             response: Response = await original_route_handler(request)
#             finish_time = time.perf_counter()
#             process_time = finish_time - start_time
#
#             response_body_dict = json.loads(response.body.decode("utf-8"))
#             success = response_body_dict.get("success")
#             error = response_body_dict.get("error", False)
#             user = response_body_dict.pop("user")
#
#             request_body = await request.body()
#             data = {
#                 "success": success,
#                 "status_code": response.status_code,
#                 "error": error,
#                 "execution_time": execution_time,
#                 "process_time": round(process_time, 4),
#                 "user": user,
#                 "method": request.method,
#                 "endpoint": request.url.path,
#                 "request": {
#                     "headers": dict(request.headers),
#                     "params": dict(MultiDict(parse_qsl(request.url.query, keep_blank_values=True))),
#                     "body": json.loads(request_body.decode("utf-8"))
#                     if len(request_body)
#                     else request_body.decode("utf-8"),
#                 },
#                 "response": {
#                     "headers": dict(response.headers),
#                     "body": response_body_dict,
#                 },
#             }
#
#             tasks = BackgroundTasks()
#             tasks.add_task(write_log, data=data)
#             response.background = tasks
#             return response
#
#         return custom_route_handler
#
# app_v1 = FastAPI()
# app_v1.router.route_class = LogRoute
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
#
#
# async def write_log(data):
#     """Logs all the available information for a normal response"""
#     log_file = tools.config.options.get("logfile")
#     if not log_file:
#         return
#
#     working_dir = "/".join(log_file.split("/")[0:-1])
#     file_path = working_dir + "/fastapi-log-current.jsonl"
#     with jsonlines.open(file_path, mode="a") as current_log:
#         current_log.write(data)
#
#
# def get_user_odoo(
#     token: Annotated[str, Depends(oauth2_scheme)],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#     )
#     try:
#         param = get_param_token(env)
#         payload = jwt.decode(token, param.get("secret_token"), algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(login=username)
#     except Exception:
#         raise credentials_exception
#     user = get_user(login=token_data.login, env=env)
#
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Not found user"
#         )
#
#     if not user.active:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
#         )
#
#     if user.last_signin_at and user.last_signin_at > datetime.fromtimestamp(
#         payload.get("iat") + 1
#     ):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Token was expired"
#         )
#     return user
#
#
# @app_v1.get("/")
# def get_docs():
#     return RedirectResponse("/api/v1/docs")
#
#
# @app_v1.post("/token", response_model=Token)
# def get_token(
#     form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     try:
#         user = authenticate_user(form_data.username, form_data.password, env)
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Invalid username or password",
#             )
#         return create_token(data={"sub": form_data.username, "iat": datetime.utcnow()}, env=env)
#
#     except AccessDenied as ad:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#         ) from ad
#
#
# @app_v1.get("/refresh_token", status_code=status.HTTP_200_OK, response_model=Token)
# async def refresh_token(
#     refresh_token: str,
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     return get_access_token(refresh_token, env=env)
#
#
# @app_v1.post("/reset_password", status_code=status.HTTP_200_OK, response_model=ResponseModel)
# async def reset_password(
#     body: ChangePassword, current_user: Annotated[Users, Depends(get_user_odoo)]
# ):
#     if body.new_password == body.confirm_password:
#         current_user.write(
#             {"password": body.confirm_password, "last_signin_at": datetime.utcnow()}
#         )
#         return {"success": True, "result": None}
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Password not match"
#         )
#
#
# @app_v1.get("/user", response_model=ResponseModel)
# def get_current_user(
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     fields:  Optional[str] = None,
# ):
#     try:
#         if not fields:
#             fields = ["id", "display_name"]
#         else:
#             fields = fields.replace(" ", "").split(",")
#
#         return {
#             "success": True,
#             "result": OdooModel.model_validate(
#                 current_user, context={"fields": fields}
#             ),
#         }
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         )
#
#
# @app_v1.get("/search_read", response_model=ResponseModels)
# def search_read(
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
#     model: str,
#     fields: str,
#     domain: Optional[str] = [],
#     order: Optional[str] = None,
#     page_index: Optional[int] = 0,
#     page_size: Optional[int] = 10,
# ):
#     try:
#         if not fields:
#             fields = ["id", "display_name"]
#         else:
#             fields = fields.replace(" ", "").split(",")
#
#         if not domain:
#             domain = []
#         else:
#             domain = safe_eval(domain)
#
#         current_env = env[model].with_user(current_user.id)
#         return {
#             "success": True,
#             "total": current_env.search_count(domain),
#             "user": {"id": current_user.id, "name": current_user.name},
#             "result": [
#                 OdooModel.model_validate(record, context={"fields": fields})
#                 for record in current_env.search(
#                     domain, offset=page_index * page_size, limit=page_size, order=order
#                 )
#             ],
#         }
#
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.get("/read", response_model=ResponseModel)
# def read_record(
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
#     model: str,
#     id: int,
#     fields: str,
# ):
#     try:
#         if not fields:
#             fields = ["id", "display_name"]
#         else:
#             fields = fields.replace(" ", "").split(",")
#         record = env[model].with_user(current_user.id).browse(id)
#         return {
#             "success": True,
#             "user": {"id": current_user.id, "name": current_user.name},
#             "result": (
#                 OdooModel.model_validate(record[0], context={"fields": fields})
#                 if len(record)
#                 else {}
#             ),
#         }
#
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.post("/create", response_model=ResponseModel)
# def create_record(
#     body: CreateParams,
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     try:
#         current_env = env[body.model].with_user(current_user.id)
#         context = dict(current_env._context)
#         context.update(body.context or {})
#         record = current_env.with_context(context).create(body.vals)
#
#         fields = body.fields.replace(" ", "").split(",") if body.fields else []
#         return {
#             "success": True,
#             "user": {"id": current_user.id, "name": current_user.name},
#             "records":
#                 OdooModel.model_validate(record, context={"fields": fields})
#                 if fields else None,
#             "result": [record.id],
#         }
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.post("/multi_create", response_model=ResponseModel)
# def create_multi_record(
#     body: CreateMultiParams,
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     try:
#         current_env = env[body.model].with_user(current_user.id)
#         context = dict(current_env._context)
#         context.update(body.context or {})
#
#         fields = body.fields.replace(" ", "").split(",") if body.fields else []
#         result_create = current_env.with_context(context).create(body.vals_list)
#         return {
#             "success": True,
#             "user": {"id": current_user.id, "name": current_user.name},
#             "records": [
#                         OdooModel.model_validate(record, context={"fields": fields})
#                         for record in result_create
#                     ]
#                 if fields else None,
#             "result": result_create.ids,
#         }
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.put("/write", response_model=ResponseModel)
# def update_record(
#     body: UpdateParams,
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     try:
#         current_env = env[body.model].with_user(current_user.id)
#         context = dict(current_env._context)
#         context.update(body.context or {})
#
#         records = current_env.with_context(context).browse(body.ids)
#         fields = body.fields.replace(" ", "").split(",") if body.fields else []
#         return {
#             "success": records.write(body.vals),
#             "user": {"id": current_user.id, "name": current_user.name},
#             "records": [
#                     OdooModel.model_validate(record, context={"fields": fields})
#                     for record in current_env.with_context(context).browse(body.ids)
#             ] if fields else None,
#             "result": None,
#         }
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.delete("/unlink", response_model=ResponseModel)
# def unlink_record(
#     body: DeleteParams,
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     try:
#         current_env = env[body.model].with_user(current_user.id)
#         context = dict(current_env._context)
#         context.update(body.context or {})
#         records = current_env.with_context(context).browse(body.ids)
#
#         return {
#             "success": records.unlink(),
#             "user": {"id": current_user.id, "name": current_user.name},
#             "result": None,
#         }
#
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.post("/call_method", response_model=ResponseModel)
# def call_method(
#     body: MethodParams,
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
# ):
#     try:
#         current_env = env[body.model].with_user(current_user.id)
#         context = dict(current_env._context)
#         context.update(body.context or {})
#         model = current_env.with_context(context)
#         fields = body.fields.replace(" ", "").split(",") if body.fields else []
#
#         args = body.args
#         if body.ids:
#             args.insert(0, body.ids)
#         return_method = call_kw(model, body.method, args, body.kwargs)
#
#         records = None
#         if body.ids and fields:
#             records = [
#                     OdooModel.model_validate(record, context={"fields": fields})
#                     for record in current_env.with_context(context).browse(body.ids)
#                 ]
#         return {
#             "success": True,
#             "user": {"id": current_user.id, "name": current_user.name},
#             "records":records,
#             "result": return_method,
#         }
#
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
#
# @app_v1.get("/attachment")
# def get_attachment(
#     current_user: Annotated[Users, Depends(get_user_odoo)],
#     env: Annotated[Environment, Depends(odoo_env)],
#     model: str = "ir.attachment",
#     id: Optional[int] = None,
#     field: Optional[str] = None,
# ):
#     try:
#         current_env = env[model].with_user(current_user.id)
#         if model == "ir.attachment":
#             attachment = current_env.browse(id)
#             if not attachment.id:
#                 return None
#
#             elif attachment.db_datas:
#                 binary_decode = base64.b64decode(attachment.raw)
#                 return StreamingResponse(
#                     io.BytesIO(binary_decode), media_type=guess_mimetype(binary_decode)
#                 )
#             return RedirectResponse(attachment.url)
#
#         else:
#             record = current_env.browse(id)
#             if not record.id or not field or not record[field]:
#                 return None
#
#             binary_decode = base64.b64decode(record[field])
#             media_type = guess_mimetype(binary_decode)
#             if media_type == "image/svg+xml":
#                 return None
#
#             return StreamingResponse(
#                 io.BytesIO(binary_decode), media_type=media_type
#             )
#
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#             user={"id": current_user.id, "name": current_user.name}
#         )
#
# @app_v1.get("/video")
# def get_video(
#     env: Annotated[Environment, Depends(odoo_env)],
#     token: Optional[str] = None,
#     range: str= Header(None)
# ):
#     start, end = range.replace("bytes=","").split("-")
#     start = int(start)
#     end = int(end) if end else start + (1024*1024)
#     try:
#         query = f"""
#             SELECT
#                 id
#             FROM
#                 ir_attachment ia
#             WHERE
#                 ia.access_token = '{token}'
#         """
#         env.cr.execute(query)
#         attachment_id = env.cr.fetchone()
#         attachment =  env["ir.attachment"].sudo().browse(attachment_id)
#         if not attachment.id:
#             return None
#         elif attachment.datas:
#             binary_decode = base64.b64decode(attachment.datas)
#         video = io.BytesIO(binary_decode)
#         video.seek(start)
#         data = video.read(end- start)
#         filesize = str(len(video.getvalue()))
#         headers = {
#             'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
#             'Accept-Ranges': 'bytes'
#         }
#         return Response(data, status_code=206, headers=headers, media_type="video/mp4")
#     except Exception as e:
#         return odoo_exception_handler(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             reason=str(e),
#         )
#
# @app_v1.get("/config_parameter", response_model=ResponseModel)
# def get_config_parameter(
#     env: Annotated[Environment, Depends(odoo_env)],
#     param: str,
# ):
#     try:
#         parameter = env["ir.config_parameter"].sudo().get_param(param)
#         if not parameter:
#             raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     reason=" Not found param"
#                 )
#         return {
#             "success": True,
#             "result":parameter
#         }
#
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         )
#
# @app_v1.get("/file")
# def get_file_attach(
#     env: Annotated[Environment, Depends(odoo_env)],
#     token:str
# ):
#     try:
#         query = f"""
#             SELECT
#                 id
#             FROM
#                 ir_attachment ia
#             WHERE
#                 ia.access_token = '{token}'
#         """
#         env.cr.execute(query)
#         attachment_id=  env.cr.fetchone()
#         file_attachs_data =  env["ir.attachment"].sudo().browse(attachment_id)
#         if not file_attachs_data:
#             raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = "file not found")
#
#         return StreamingResponse(
#             io.BytesIO(base64.b64decode(file_attachs_data.datas)),
#             media_type=file_attachs_data.mimetype
#         )
#     except MissingError as e:
#         raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Value not found")
#     except Exception as e:
#         raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))
#
# app.mount("/api/v1", app_v1)
# odoo_routes += ["/api/v1" + route.path for route in app_v1.routes]
#
# ############### End Define Router V1 ###############
# app_v2 = FastAPI()
#
#
# @app_v2.get("/")
# def get_docs():
#     return RedirectResponse("/api/v2/docs")
#
#
# @app_v2.get("/demo")
# def get_hello():
#     return {"sub_app": "demo"}
#
#
# app.mount("/api/v2", app_v2)
# odoo_routes += ["/api/v2" + route.path for route in app_v2.routes]
#
# ############### End Define Router V2 ###############

# -*- coding:utf-8 -*-
import base64
import io
import json
import time
from datetime import datetime
from typing import Callable, Optional
from urllib.parse import parse_qsl

from fastapi import (BackgroundTasks, Depends, FastAPI, Header, HTTPException,
                     Request, Response, status)
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from odoo import tools
from odoo.addons.base.models.res_users import Users
from odoo.api import Environment, call_kw
from odoo.exceptions import AccessDenied, MissingError
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.safe_eval import safe_eval
from starlette.datastructures import MultiDict

from .dependencies import (ALGORITHM, authenticate_user, create_token,
                           get_access_token, get_param_token, get_user,
                           odoo_env, odoo_exception_handler)
from .schemas import (ChangePassword, CreateMultiParams, CreateParams,
                      DeleteParams, MethodParams, OdooModel, ResponseModel,
                      ResponseModels, Token, TokenData, UpdateParams)

# Configuración de la aplicación y variables globales
app = FastAPI()
app_v1 = FastAPI()
app_v2 = FastAPI()
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 30 * 6
odoo_routes = []
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

############### Middleware de Logs ###############

class LogRoute(APIRoute):
    """Middleware para capturar y registrar información de solicitudes."""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            if request.url.path not in [
                "/api/v1/search_read", "/api/v1/read", "/api/v1/create",
                "/api/v1/multi_create", "/api/v1/write", "/api/v1/unlink",
                "/api/v1/call_method"
            ]:
                return await original_route_handler(request)

            start_time = time.perf_counter()
            response: Response = await original_route_handler(request)
            process_time = round(time.perf_counter() - start_time, 4)

            try:
                request_body = await request.body()
                response_body = json.loads(response.body.decode("utf-8"))
                log_data = {
                    "method": request.method,
                    "endpoint": request.url.path,
                    "process_time": process_time,
                    "status_code": response.status_code,
                    "request": {
                        "headers": dict(request.headers),
                        "params": dict(MultiDict(parse_qsl(request.url.query))),
                        "body": json.loads(request_body.decode("utf-8")) if request_body else {}
                    },
                    "response": {
                        "headers": dict(response.headers),
                        "body": response_body
                    }
                }
                BackgroundTasks().add_task(write_log, log_data)
            except Exception:
                pass
            return response

        return custom_route_handler


async def write_log(data):
    """Guarda logs en un archivo JSONL de manera asíncrona."""
    log_file = tools.config.options.get("logfile")
    if not log_file:
        return

    file_path = f"{'/'.join(log_file.split('/')[:-1])}/fastapi-log-current.jsonl"
    async with aiofiles.open(file_path, mode="a") as current_log:
        await current_log.write(json.dumps(data) + "\n")

############### Funciones Utilitarias ###############

def validate_fields(fields: Optional[str]) -> list:
    """Valida y convierte una cadena de campos en una lista."""
    return fields.replace(" ", "").split(",") if fields else ["id", "display_name"]

############### Endpoints Generales ###############

@app_v1.get("/")
def get_docs():
    return RedirectResponse("/api/v1/docs")


@app_v1.post("/token", response_model=Token)
def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    env: Annotated[Environment, Depends(odoo_env)]
):
    """Genera un token para autenticación."""
    try:
        user = authenticate_user(form_data.username, form_data.password, env)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return create_token(data={"sub": form_data.username, "iat": datetime.utcnow()}, env=env)
    except AccessDenied:
        raise HTTPException(status_code=401, detail="Incorrect username or password")


@app_v1.get("/user", response_model=ResponseModel)
def get_current_user(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    fields: Optional[str] = None,
):
    """Obtiene información del usuario actual."""
    try:
        validated_fields = validate_fields(fields)
        return {
            "success": True,
            "result": OdooModel.model_validate(
                current_user, context={"fields": validated_fields}
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

############### Operaciones de Modelo Odoo ###############

@app_v1.get("/search_read", response_model=ResponseModels)
def search_read(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    model: str,
    fields: str,
    domain: Optional[str] = "[]",
    order: Optional[str] = None,
    page_index: Optional[int] = 0,
    page_size: Optional[int] = 10,
):
    """Busca y lee registros de un modelo en Odoo."""
    try:
        validated_fields = validate_fields(fields)
        domain_eval = safe_eval(domain)
        model_env = env[model].with_user(current_user.id)

        records = model_env.search(
            domain_eval, offset=page_index * page_size, limit=page_size, order=order
        )
        return {
            "success": True,
            "total": model_env.search_count(domain_eval),
            "result": [
                OdooModel.model_validate(record, context={"fields": validated_fields})
                for record in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app_v1.get("/read", response_model=ResponseModel)
def read_record(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    model: str,
    id: int,
    fields: str,
):
    """Lee un único registro en Odoo."""
    try:
        validated_fields = validate_fields(fields)
        record = env[model].with_user(current_user.id).browse(id)
        return {
            "success": True,
            "result": OdooModel.model_validate(
                record, context={"fields": validated_fields}
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

############### Configuración y Montaje de Subaplicaciones ###############

app_v1.router.route_class = LogRoute
app.mount("/api/v1", app_v1)

@app_v2.get("/")
def get_docs_v2():
    return RedirectResponse("/api/v2/docs")

@app_v2.get("/demo")
def demo_endpoint():
    return {"sub_app": "demo"}

app.mount("/api/v2", app_v2)
odoo_routes += ["/api/v1" + route.path for route in app_v1.routes]
odoo_routes += ["/api/v2" + route.path for route in app_v2.routes]
