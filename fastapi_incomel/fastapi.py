# -*- coding:utf-8 -*-

import base64
import io
import re
import sys
import pytz
from datetime import datetime
from typing import Callable, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import logging
_logger = logging.getLogger(__name__)
import json
import time
from urllib.parse import parse_qsl

import jsonlines
import jwt
from fastapi import (BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query,
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
from starlette.types import Message

from .dependencies import (ALGORITHM, authenticate_user, create_token,
                           get_access_token, get_param_token, get_user,
                           odoo_env, odoo_exception_handler)
from .schemas import (ChangePassword, CreateMultiParams, CreateParams,
                      DeleteParams, MethodParams, OdooModel, ResponseModel,
                      ResponseModels, Token, TokenData, UpdateParams)

app = FastAPI()
odoo_routes = []
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 30 * 6
############### Define Router V1 ###############

class LogRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            if not request.url.path in [
                "/api/v1/search_read",
                "/api/v1/read",
                "/api/v1/create",
                "/api/v1/multi_create",
                "/api/v1/write",
                "/api/v1/unlink",
                "/api/v1/call_method",
            ]:
                return await original_route_handler(request)

            execution_time = datetime.now().isoformat()
            start_time = time.perf_counter()
            response: Response = await original_route_handler(request)
            finish_time = time.perf_counter()
            process_time = finish_time - start_time

            response_body_dict = json.loads(response.body.decode("utf-8"))
            success = response_body_dict.get("success")
            error = response_body_dict.get("error", False)
            user = response_body_dict.pop("user")

            request_body = await request.body()
            data = {
                "success": success,
                "status_code": response.status_code,
                "error": error,
                "execution_time": execution_time,
                "process_time": round(process_time, 4),
                "user": user,
                "method": request.method,
                "endpoint": request.url.path,
                "request": {
                    "headers": dict(request.headers),
                    "params": dict(MultiDict(parse_qsl(request.url.query, keep_blank_values=True))),
                    "body": json.loads(request_body.decode("utf-8"))
                    if len(request_body)
                    else request_body.decode("utf-8"),
                },
                "response": {
                    "headers": dict(response.headers),
                    "body": response_body_dict,
                },
            }

            tasks = BackgroundTasks()
            tasks.add_task(write_log, data=data)
            response.background = tasks
            return response

        return custom_route_handler

app_v1 = FastAPI()
app_v1.router.route_class = LogRoute
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


async def write_log(data):
    """Logs all the available information for a normal response"""
    log_file = tools.config.options.get("logfile")
    if not log_file:
        return

    working_dir = "/".join(log_file.split("/")[0:-1])
    file_path = working_dir + "/fastapi-log-current.jsonl"
    with jsonlines.open(file_path, mode="a") as current_log:
        current_log.write(data)


def get_user_odoo(
    token: Annotated[str, Depends(oauth2_scheme)],
    env: Annotated[Environment, Depends(odoo_env)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        param = get_param_token(env)
        payload = jwt.decode(token, param.get("secret_token"), algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(login=username)
    except Exception:
        raise credentials_exception
    user = get_user(login=token_data.login, env=env)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not found user"
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )

    if user.last_signin_at and user.last_signin_at > datetime.fromtimestamp(
        payload.get("iat") + 1
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token was expired"
        )
    return user


@app_v1.get("/")
def get_docs():
    return RedirectResponse("/api/v1/docs")

@app_v1.post("/token", response_model=Token)
def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    env: Annotated[Environment, Depends(odoo_env)],
):
    try:
        user = authenticate_user(form_data.username, form_data.password, env)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid username or password",
            )
        return create_token(data={"sub": form_data.username, "iat": datetime.utcnow()}, env=env)

    except AccessDenied as ad:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        ) from ad


@app_v1.get("/search_read", response_model=ResponseModels)
def search_read(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    model: str,
    fields: str,
    domain: Optional[str] = [],
    order: Optional[str] = None,
    page_index: Optional[int] = 0,
    page_size: Optional[int] = 10,
):
    try:
        if not fields:
            fields = ["id", "display_name"]
        else:
            fields = fields.replace(" ", "").split(",")

        if not domain:
            domain = []
        else:
            domain = safe_eval(domain)

        current_env = env[model].with_user(current_user.id)
        return {
            "success": True,
            "total": current_env.search_count(domain),
            "user": {"id": current_user.id, "name": current_user.name},
            "result": [
                OdooModel.model_validate(record, context={"fields": fields})
                for record in current_env.search(
                    domain, offset=page_index * page_size, limit=page_size, order=order
                )
            ],
        }

    except Exception as e:
        return odoo_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            reason=str(e),
            user={"id": current_user.id, "name": current_user.name}
        )


@app_v1.get("/read", response_model=ResponseModel)
def read_record(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    model: str,
    id: int,
    fields: str,
):
    try:
        if not fields:
            fields = ["id", "display_name"]
        else:
            fields = fields.replace(" ", "").split(",")
        record = env[model].with_user(current_user.id).browse(id)
        return {
            "success": True,
            "user": {"id": current_user.id, "name": current_user.name},
            "result": (
                OdooModel.model_validate(record[0], context={"fields": fields})
                if len(record)
                else {}
            ),
        }

    except Exception as e:
        return odoo_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            reason=str(e),
            user={"id": current_user.id, "name": current_user.name}
        )
 
@app_v1.get("/ubicaciones")
def get_ubicaciones(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    model: str = "stock.location",
    id: Optional[int] = None,
    name_like: Optional[str] = None,
):
    try:
        current_env = env[model].with_user(current_user.id)
        domain = [('usage', '=', 'internal')]


        if id:
            domain.append(("id", "=", id))
        if name_like:
            domain.append(("name", "ilike", name_like))

        print("Domain: ", domain)
        ubicaciones = current_env.search(domain)
        print("Ubicaciones: ", ubicaciones)

        if not ubicaciones:
            return {
                "success": True,
                "user": {"id": current_user.id, "name": current_user.name},
                "result": []
            }

        # Leer los datos de las ubicaciones encontradas
        print("Ubicaciones Data: ", ubicaciones)

        # ubicaciones_data = current_env.read(ubicaciones, fields=["id", "name"])
        ubicaciones_data = []
        for ubicacion_id in ubicaciones:
            print("Ubicacion ID: ", ubicacion_id)
            print("Ubicacion ID: ", ubicacion_id.name)
            print("quant_ids ID: ", ubicacion_id.quant_ids)
            
            
            ubicaciones_data.append({
                "id": ubicacion_id.id,
                "name": ubicacion_id.name,
                # Agrega aquí otros campos que necesites
            })
        
        print("Ubicaciones Data: ", ubicaciones_data)

        return {
            "success": True,
            "user": {"id": current_user.id, "name": current_user.name},
            "result": ubicaciones_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app_v1.get("/productosXubicaciones")
def get_productosXubicaciones(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    name_almacen: Optional[str] = None,
    name_ubicacion: Optional[str] = None,
    name_product: Optional[str] = None,
    code_product: Optional[str] = None,
    id: Optional[int] = None,
):
    try:
        model = "stock.location"
        model_almacen = "stock.warehouse"
        product_env = env["product.template"].with_user(current_user.id)

        domain_almacen = [("name", "ilike", name_almacen)]
        _logger.info("Domain domain_almacen: %s", domain_almacen)

        search_almacen = env[model_almacen].search(domain_almacen)
        _logger.info("Domain search_almacen: %s", search_almacen)

        if not search_almacen:
            search_almacen = env[model_almacen].search([])

        if len(search_almacen) > 1 and name_almacen:
            search_almacen = env[model_almacen].search([('name', '=', name_almacen)])

        if len(search_almacen) > 1 and name_almacen and not name_product and not code_product:
            nombres_alamacenes = [alm.name for alm in search_almacen]
            return {
                "success": True,
                "user": {"id": current_user.id, "name": current_user.name},
                "result": "Se encontraron varios almacenes con los datos proporcionados, debe proporcionar datos unicos",
                "result_almacen": str(nombres_alamacenes),
            }

        ubicaciones_data = []
        lista_locaciones = []
        cantidad_total_de_producto = 0

        # Buscar lista de precios CREDITO una sola vez antes de los loops
        tz_gt = pytz.timezone('America/Guatemala')
        fecha_gt = datetime.now(tz_gt)
        pricelist = env["product.pricelist"].with_user(current_user.id).search(
            [("active", "=", True), "|", ("name", "=ilike", "CRÉDITO"), ("name", "=ilike", "CREDITO")],
            limit=1
        )

        for almacen in search_almacen:
            _logger.info("Domain almacen modelo: %s", almacen)
            _logger.info("Domain almacen.code: %s", almacen.code)
            _logger.info("Domain almacen.name: %s", almacen.name)

            search_location = env['stock.location'].with_user(current_user.id).search([('warehouse_id', '=', almacen.id)])
            _logger.info("Domain search_location: %s", search_location)

            if not search_location:
                return {
                    "success": True,
                    "user": {"id": current_user.id, "name": current_user.name},
                    "result": "No se encontro la ubicacion con los datos proporcionados en el almacen %s" % (almacen.code)
                }

            for ubicacion_id in search_location.filtered(lambda l: l.usage == 'internal'):
                if name_ubicacion and name_ubicacion.lower() not in ubicacion_id.name.lower():
                    continue
                if ubicacion_id.id in lista_locaciones:
                    continue

                productos_agrupados = {}  # Clave: product_id.id para no perder productos sin default_code

                for quant_id in ubicacion_id.quant_ids:
                    producto_id = quant_id.product_id
                    prod_code = producto_id.default_code or ""  # Fix Bug 2: evitar .lower() sobre False

                    if name_product or code_product:
                        if name_product and name_product.lower() not in producto_id.name.lower():
                            continue
                        if code_product and code_product.lower() not in prod_code.lower():
                            continue

                    prod_key = producto_id.id  # Fix Bug 1: usar ID como clave, no default_code
                    if prod_key not in productos_agrupados:
                        # Fix precio: CREDITO → lst_price variante → list_price ficha
                        if pricelist:
                            precio = pricelist.with_context(date=fecha_gt)._get_product_price(producto_id, 1.0)
                        else:
                            precio = 0.0
                        if not precio or precio <= 0:
                            precio = producto_id.lst_price or producto_id.list_price or 0.0

                        productos_agrupados[prod_key] = {
                            "Almacen ID": almacen.id,
                            "Almacen Code": almacen.code,
                            "Nombre Almacen": almacen.name,
                            "Nombre": producto_id.name,
                            "Familia": producto_id.full_category_path.split("/")[0] if "/" in producto_id.full_category_path else producto_id.full_category_path,
                            "Genérico": producto_id.categ_id.name,
                            "Marca": producto_id.x_studio_marca,
                            "Modelo": producto_id.x_studio_modelo,
                            "Articulo": producto_id.barcode,
                            "default_code": prod_code,
                            "Cantidad_inventario": 0,
                            "Cantidad_disponible": 0,
                            "Cantidad_reservado": 0,
                            "Stock": 0,
                            "POE": precio,
                        }

                    # Fix Bug 3: usar quantity (stock real) en vez de inventory_quantity_auto_apply
                    productos_agrupados[prod_key]["Cantidad_inventario"] += quant_id.quantity
                    productos_agrupados[prod_key]["Cantidad_disponible"] += quant_id.available_quantity
                    productos_agrupados[prod_key]["Cantidad_reservado"] += quant_id.reserved_quantity
                    productos_agrupados[prod_key]["Stock"] += quant_id.quantity

                    cantidad_total_de_producto += quant_id.quantity

                lista_productos = list(productos_agrupados.values())

                ubicaciones_data.append({
                    "id_ubicacion": ubicacion_id.id,
                    "almacen_id": almacen.id,
                    "almacen": almacen.name,
                    "almacen_code": almacen.code,
                    "ubicacion": ubicacion_id.name,
                    'lista_productos': lista_productos,
                })

        return {
            "success": True,
            "user": {"id": current_user.id, "name": current_user.name},
            "result": ubicaciones_data,
            "total_productos": cantidad_total_de_producto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app_v1.get("/FacturasXubicaciones")
def get_facturasXubicaciones(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    # date_from:  str = Query(..., description="Fecha desde es requerida MM/DD/YYYY or DD/MM/YYYY"),
    date_from:  str = None,
    date_to:  str = None,
    name_agencia: Optional[str] = Query(None, description="Nombre Agencia"),
    factura_name: Optional[str] = Query(None, description="Factura con Prefijo"),
    factura_number: Optional[int] = None,
    factura_id: Optional[str] = None,
    DPI: Optional[str] =  Query(None, description="Nro de Identidad"),
):
    try:

        model  = "res.partner"
        partner_id_env = env[model].with_user(current_user.id)
        partner_id = False


        if DPI:
            domain = [('vat', '=', DPI)]
            partner_id = partner_id_env.search(domain)
            if not partner_id:
                domain = [('documento_personal_identificacion', '=',  DPI )]
                partner_id = partner_id_env.search(domain)
            if not partner_id:
                domain = [('pasaporte', '=',  DPI )]
                partner_id = partner_id_env.search(domain)
            
            if not partner_id:
                return {
                    "success": False,
                    "message": "No se encontro el DPI, VAT, NIT o Pasaporte, recuerda que el campo DPI debe ser exacto, sin espacios ni caracteres especiales, verifique en odoo",
                    "result": []
                }
            if len(partner_id) > 1:
                return {
                    "success": False,
                    "message": "Se encontraron varios DPI verifique en odoo",
                    "result": []
                }

        model  = "account.move"
        current_env = env[model].with_user(current_user.id)
        # domain = [('usage', '=', 'internal')]
        domain = [('state', 'in', ['posted', 'paid' , 'done']) , 
                   ('move_type', 'in', ['out_invoice', 'out_refund' , 'out_receipt' ] ) ]
        if partner_id:
            domain.append(("partner_id", "=", partner_id.id))
        
        if  date_from: 
            domain.append(("date", ">=", date_from))
        if  date_to:
            print("date_to!!!!!: ", date_to)
            domain.append(("date", "<=", date_to))



        if name_agencia:

            domain_journal =[("name", "=", name_agencia)]
            current_journal = env['account.journal'].with_user(current_user.id).search(domain_journal)
            domain.append(("journal_id", "=", current_journal.id))


        if factura_name:
            domain.append(("name", "ilike", factura_name))

        elif factura_number:
            domain.append(("sequence_number", "=", factura_number))

        elif factura_id:
            domain.append(("id", "=", factura_id))
        print("domain!!!!: ", domain)

        facturas = current_env.search(domain)

        if not facturas:
            return {
                "success": True,
                "user": {"id": current_user.id, "name": current_user.name},
                "result": []
            }

        # ubicaciones_data = current_env.read(ubicaciones, fields=["id", "name"])
        facturas_data = []
        for factura_id in facturas:
            tipo_venta = ""
            if factura_id.move_type == 'out_invoice':
                tipo_venta = 'Factura'
            else:
                tipo_venta = 'Nota de Crédito'  

            lista_productos = []
            for line_id in factura_id.invoice_line_ids:
                lista_productos.append({
                    "name": line_id.product_id.name, #Nombre del Artículo
                    "default_code": line_id.product_id.default_code, # Código por defecto
                    "barcode": line_id.product_id.barcode, # Código de barras
                    "Descripción": line_id.name, # Descripción del Artículo
                    "Cantidad": line_id.quantity, # Cantidad disponible en esa ubicación
                    "Precio": line_id.price_unit, # Precio en lista de precios general
                    'tipo_venta':tipo_venta, #Tipo (Facturas, Notas de Crédito)
                })
            try:
                fel_serie = factura_id.fel_serie
                fel_numero = factura_id.fel_numero
            except:
                fel_serie = ""
                fel_numero = ""
                
            facturas_data.append({

                "date": factura_id.date, #Fecha de la Factura
                "ciudadCliente": factura_id.partner_id.city, #Fecha de la Factura
                "vendedor": factura_id.user_id.name, #vendedor
                "Journal_name": factura_id.journal_id.name, #Agencia donde se realizó la Factura
                'name':factura_id.name, #TRX (Id de la Transacción)
                "numero": factura_id.sequence_number, #Numero de la factura

                'trx_id':factura_id.id, #TRX (Id de la Transacción)
                'total':factura_id.amount_total, #Total (monto total de la factura)
                'fpago':factura_id.x_studio_lista_de_precio_1.name, #F.Pago (Método de pago)
                'identification':factura_id.partner_id.documento_personal_identificacion, #Identificación del Cliente
                'cliente':factura_id.partner_id.name, #Nombre del Cliente
                'tipo':tipo_venta, #Tipo (Facturas, Notas de Crédito)
                'tipo_venta':tipo_venta, #Tipo (Facturas, Notas de Crédito)
                'Plazo':factura_id.Plazo, #Tipo (Facturas, Notas de Crédito)
                'serie': fel_serie or "VERIFICAR CAMPO fel_serie", #Serie (Serie de la Factura)
                'canal': fel_numero or "VERIFICAR CAMPO fel_numero", #Canal (Canal de la Factura) fel_numero

                #Datos de la Autorización
                'nro_autorizacion': factura_id.char_autorization_netfinance,
                'DpiCliente_autorizado': factura_id.DpiCliente_autorizado,
                'Factura_monto_autorizado': factura_id.Factura_monto_autorizado,
                'Pagare_monto_autorizado': factura_id.Pagare_monto_autorizado,
                'Agencia_Autorizada': factura_id.Agencia_autorizada,
                'IdPersona_autorizada': factura_id.IdPersona_autorizada,
                'cuota_autorizada': factura_id.cuota_autorizada,
                'porcentaje_descuento_autorizado': factura_id.porcentaje_descuento_autorizado,
                'tipo_cliente_autorizado': factura_id.tipo_cliente_autorizado,
                'monto_plus_autorizado': factura_id.monto_plus_autorizado,
                'enganche_autorizado': factura_id.enganche_autorizado,
                'nro_items_invoice':factura_id.nro_items_invoice,
                'lista_productos': lista_productos,
                'TipoFlujo': factura_id.TipoFlujo,


                # Agrega aquí otros campos que necesites
            })

        return {
            "success": True,
            "user": {"id": current_user.id, "name": current_user.name},
            "result": facturas_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@app_v1.get("/FacturasXautorizaciones")
def get_facturasXautorizaciones(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    nro_autorizacion:  str = Query(..., description="Nro de Autorizacion"),
):
    try:

        model  = "res.partner"

        model  = "account.move"
        current_env = env[model].with_user(current_user.id)
        # domain = [('usage', '=', 'internal')]
        domain = [('char_autorization_netfinance', '=', nro_autorizacion)]
          
        facturas = current_env.search(domain)

        if not facturas:
            return {
                "success": True,
                "user": {"id": current_user.id, "name": current_user.name},
                "result": []
            }

        # ubicaciones_data = current_env.read(ubicaciones, fields=["id", "name"])
        facturas_data = []
        for factura_id in facturas:
            tipo_venta = ""
            if factura_id.move_type == 'out_invoice':
                tipo_venta = 'Factura'
            else:
                tipo_venta = 'Nota de Crédito'  

            lista_productos = []
            for line_id in factura_id.invoice_line_ids:
                lista_productos.append({
                    "name": line_id.product_id.name, #Nombre del Artículo
                    "default_code": line_id.product_id.default_code, # Código por defecto
                    "barcode": line_id.product_id.barcode, # Código de barras
                    "Descripción": line_id.name, # Descripción del Artículo
                    "Cantidad": line_id.quantity, # Cantidad disponible en esa ubicación
                    "Precio": line_id.price_unit, # Precio en lista de precios general
                    'tipo_venta':tipo_venta, #Tipo (Facturas, Notas de Crédito)
                })
            try:
                fel_serie = factura_id.fel_serie
                fel_numero = factura_id.fel_numero
            except:
                fel_serie = ""
                fel_numero = ""
                
            facturas_data.append({

                "date": factura_id.date, #Fecha de la Factura
                "ciudadCliente": factura_id.partner_id.city, #Fecha de la Factura
                "vendedor": factura_id.user_id.name, #vendedor
                "Journal_name": factura_id.journal_id.name, #Agencia donde se realizó la Factura
                'name':factura_id.name, #TRX (Id de la Transacción)
                'trx_id':factura_id.id, #TRX (Id de la Transacción)
                'total':factura_id.amount_total, #Total (monto total de la factura)
                'fpago':factura_id.x_studio_lista_de_precio_1.name, #F.Pago (Método de pago)
                'identification':factura_id.partner_id.documento_personal_identificacion, #Identificación del Cliente
                'cliente':factura_id.partner_id.name, #Nombre del Cliente
                'tipo':tipo_venta, #Tipo (Facturas, Notas de Crédito)
                'plazo':factura_id.Plazo, #Tipo (Facturas, Notas de Crédito)
                'serie': fel_serie or "VERIFICAR CAMPO fel_serie", #Serie (Serie de la Factura)
                'canal': fel_numero or "VERIFICAR CAMPO fel_numero", #Canal (Canal de la Factura) fel_numero

                #Datos de la Autorización
                'nro_autorizacion': factura_id.char_autorization_netfinance,
                'DpiCliente_autorizado': factura_id.DpiCliente_autorizado,
                'Factura_monto_autorizado': factura_id.Factura_monto_autorizado,
                'Pagare_monto_autorizado': factura_id.Pagare_monto_autorizado,
                'Agencia_Autorizada': factura_id.Agencia_autorizada,
                'IdPersona_autorizada': factura_id.IdPersona_autorizada,
                'cuota_autorizada': factura_id.cuota_autorizada,
                'porcentaje_descuento_autorizado': factura_id.porcentaje_descuento_autorizado,
                'tipo_cliente_autorizado': factura_id.tipo_cliente_autorizado,
                'monto_plus_autorizado': factura_id.monto_plus_autorizado,
                'enganche_autorizado': factura_id.enganche_autorizado,
                'nro_items_invoice':factura_id.nro_items_invoice,
                'lista_productos': lista_productos,
                'TipoFlujo': factura_id.TipoFlujo,


                # Agrega aquí otros campos que necesites
            })

        return {
            "success": True,
            "user": {"id": current_user.id, "name": current_user.name},
            "result": facturas_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app_v1.get("/producto_codigo")
def get_producto_por_codigo(
    current_user: Annotated[Users, Depends(get_user_odoo)],
    env: Annotated[Environment, Depends(odoo_env)],
    codigo: str = Query(..., description="Código de barras o referencia interna"),
):
    try:
        # 1. LIMPIEZA DEL CÓDIGO DE BÚSQUEDA
        codigo = re.sub(r'\s+', '', codigo)

        # 2. DOMINIO DE BÚSQUEDA DE PRODUCTO (SOLO ACTIVOS)
        domain = [
            ("active", "=", True),
            "|", 
            ("barcode", "=", codigo), 
            ("default_code", "=", codigo)
        ]

        # 3. BÚSQUEDA EN VARIANTES
        producto = env["product.product"].with_user(current_user.id).search(domain, limit=1)

        # 4. FALLBACK A PLANTILLAS SI NO SE ENCONTRÓ VARIANTE
        if not producto:
            template = env["product.template"].with_user(current_user.id).search(domain, limit=1)
            if template:
                producto = template.product_variant_id

        if not producto:
            return {
                "success": False, 
                "mensaje": "Producto no encontrado", 
                "resultado": []
            }

        # ---------------------------------------------------------
        # EXTRACCIÓN DE DATOS (STUDIO Y NOMBRE LIMPIO)
        # ---------------------------------------------------------
        nombre_limpio = (producto.name or "").strip()
        
        # BÚSQUEDA DE CAMPOS STUDIO (VARIANTE > TEMPLATE) [CITE: 1.2]
        marca = producto.x_studio_marca or producto.product_tmpl_id.x_studio_marca or ""
        modelo = producto.x_studio_modelo or producto.product_tmpl_id.x_studio_modelo or ""

        # EXTRAER NOMBRE SI SON CAMPOS MANY2ONE
        if hasattr(marca, 'display_name'): marca = marca.display_name
        if hasattr(modelo, 'display_name'): modelo = modelo.display_name

        # ---------------------------------------------------------
        # LÓGICA DE PRECIOS - COMPARACIÓN FLEXIBLE Y HORA GUATEMALA
        # ---------------------------------------------------------
        # DEFINIMOS LA ZONA HORARIA LOCAL PARA VALIDAR REGLAS TEMPORALES [CITE: 1.1]
        tz_gt = pytz.timezone('America/Guatemala')
        fecha_gt = datetime.now(tz_gt)

        # EL OPERADOR '=ILIKE' BUSCA SIN IMPORTAR MAYÚSCULAS/MINÚSCULAS NI TILDES [CITE: 1.1, 1.2]
        pricelist_domain = [
            ("active", "=", True),
            "|",
            ("name", "=ilike", "CRÉDITO"),
            ("name", "=ilike", "CREDITO")
        ]
        
        pricelist = env["product.pricelist"].with_user(current_user.id).search(
            pricelist_domain, limit=1
        )

        precio = 0.0
        if pricelist:
            # INYECTAMOS EL CONTEXTO DE FECHA PARA QUE ODOO APLIQUE EL PRECIO CORRECTO [CITE: 1.1]
            precio = pricelist.with_context(date=fecha_gt)._get_product_price(producto, 1.0)
        
        # FALLBACK AL PRECIO DE LISTA SI NO HAY REGLA VIGENTE
        if not precio or precio <= 0:
            precio = producto.lst_price or producto.list_price or 0.0

        # ---------------------------------------------------------
        # JERARQUÍA DE CATEGORÍAS (4 NIVELES)
        # ---------------------------------------------------------
        niveles = []
        curr_categ = producto.categ_id
        while curr_categ:
            niveles.append(curr_categ.name)
            curr_categ = curr_categ.parent_id
        
        niveles.reverse()

        # -------------------------
        # RESPUESTA FINAL
        # -------------------------
        return {
            "success": True,
            "resultado": {
                "id": producto.id,
                "codigo_barras": producto.barcode or "",
                "nombre": nombre_limpio,
                "tipo_familia": niveles[0] if len(niveles) > 0 else "",
                "familia": niveles[1] if len(niveles) > 1 else "",
                "categoria": niveles[2] if len(niveles) > 2 else "",
                "generico": niveles[3] if len(niveles) > 3 else "",
                "marca": marca,
                "modelo": modelo,
                "POE": precio,
            }
        }

    except Exception as e:
        print(f"Error Odoo API: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

app.mount("/api/v1", app_v1)
odoo_routes += ["/api/v1" + route.path for route in app_v1.routes]

############### End Define Router V1 ###############
app_v2 = FastAPI()


@app_v2.get("/")
def get_docs():
    return RedirectResponse("/api/v2/docs")


@app_v2.get("/demo")
def get_hello():
    return {"sub_app": "demo"}


app.mount("/api/v2", app_v2)
odoo_routes += ["/api/v2" + route.path for route in app_v2.routes]

############### End Define Router V2 ###############
