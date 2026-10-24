# 	# -*- coding:utf-8 -*-
#
# from itertools import chain
# from contextlib import contextmanager
# from io import BytesIO
# from functools import partial, lru_cache, update_wrapper
#
# from a2wsgi import ASGIMiddleware
#
# from odoo import models, SUPERUSER_ID
# from odoo.http import request as odoo_request, Dispatcher
#
# from ..dependencies import odoo_env_ctx
# from ..fastapi import app as fastapp, odoo_routes
#
# try:
#     from odoo.http import HTTPRequest, make_request_wrap_methods
#
#     setattr(
#         HTTPRequest,
#         "_get_stream_for_parsing",
#         property(*make_request_wrap_methods("_get_stream_for_parsing")),
#     )
# except:
#     pass
#
# def get_routing():
#     return {
#         "type": "fastapi",
#         "auth": "public",
#         "methods": ["GET", "POST", "PUT", "DELETE"],
#         "routes": [
#             "fastapi/",
#             "fastapi/<path:application_path>",
#         ],
#         "csrf": False,
#     }
#
#
# def get_app():
#     return ASGIMiddleware(fastapp)
#
#
# class FastApiDispatcher(Dispatcher):
#     routing_type = "fastapi"
#
#     @classmethod
#     def is_compatible_with(cls, request):
#         return True
#
#     def dispatch(self, *args, **kwargs):
#         self.request.params = {}
#         environ = self._get_environ()
#         app = get_app()
#         uid = SUPERUSER_ID
#         data = BytesIO()
#         with self._manage_odoo_env(uid):
#             for r in app(environ, self._make_response):
#                 data.write(r)
#
#             response = self.request.make_response(data.getvalue(), headers=self.headers)
#             response.status = self.status
#             return response
#
#     def handle_error(self, exc):
#         pass
#
#     def _make_response(self, status_mapping, headers_tuple, content):
#         self.status = status_mapping[:3]
#         self.headers = dict(headers_tuple)
#
#     def _get_environ(self):
#         environ = self.request.httprequest.environ
#         environ["wsgi.input"] = self.request.httprequest._get_stream_for_parsing()
#         return environ
#
#     @contextmanager
#     def _manage_odoo_env(self, uid=None):
#         env = self.request.env
#         if uid:
#             env = env(user=uid)
#         token = odoo_env_ctx.set(env)
#         try:
#             yield
#         finally:
#             odoo_env_ctx.reset(token)
#
#
# class IrHttp(models.AbstractModel):
#     _inherit = "ir.http"
#
#     def _generate_routing_rules(cls, modules, converters):
#         return chain(
#             super()._generate_routing_rules(modules, converters),
#             cls._endpoint_routing_rules(),
#         )
#
#     def _endpoint_routing_rules(cls):
#         method = getattr(FastApiDispatcher(odoo_request), "dispatch")
#         endpoint = partial(method, (), {})
#         update_wrapper(endpoint, method)
#         endpoint.routing = get_routing()
#         for route in odoo_routes:
#             yield (route, endpoint)

# -*- coding:utf-8 -*-

from itertools import chain
from contextlib import contextmanager
from io import BytesIO
from functools import partial, update_wrapper

from a2wsgi import ASGIMiddleware

from odoo import models, SUPERUSER_ID
from odoo.http import request as odoo_request, Dispatcher

from ..dependencies import odoo_env_ctx


try:
    from odoo.http import HTTPRequest, make_request_wrap_methods

    # Agregar un método para obtener el flujo de entrada HTTP
    setattr(
        HTTPRequest,
        "_get_stream_for_parsing",
        property(*make_request_wrap_methods("_get_stream_for_parsing")),
    )
except ImportError:
    pass


def get_routing():
    """
    Define las reglas de enrutamiento para las rutas de FastAPI.
    """
    return {
        "type": "fastapi",
        "auth": "public",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "routes": [
            "fastapi/",
            "fastapi/<path:application_path>",
        ],
        "csrf": False,
    }


def get_app():
    """
    Devuelve la aplicación ASGI envuelta en un middleware compatible con WSGI.
    """
    from ..fastapi import app as fastapp
    return ASGIMiddleware(fastapp)


class FastApiDispatcher(Dispatcher):
    """
    Clase de Dispatcher para manejar las solicitudes de FastAPI en el contexto de Odoo.
    """
    routing_type = "fastapi"

    @classmethod
    def is_compatible_with(cls, request):
        """
        Verifica si el Dispatcher es compatible con la solicitud actual.
        """
        return True

    def dispatch(self, *args, **kwargs):
        """
        Maneja la solicitud FastAPI, integrándola con el entorno de Odoo.
        """
        self.request.params = {}
        environ = self._get_environ()
        app = get_app()
        uid = SUPERUSER_ID
        data = BytesIO()

        with self._manage_odoo_env(uid):
            for response_chunk in app(environ, self._make_response):
                data.write(response_chunk)

            response = self.request.make_response(
                data.getvalue(),
                headers=self.headers
            )
            response.status = self.status
            return response

    def handle_error(self, exc):
        """
        Método para manejar errores durante el despacho.
        Actualmente no implementa ninguna lógica personalizada.
        """
        pass

    def _make_response(self, status_mapping, headers_tuple, content):
        """
        Construye la respuesta HTTP con estado, encabezados y contenido.
        """
        self.status = status_mapping[:3]
        self.headers = dict(headers_tuple)

    def _get_environ(self):
        """
        Devuelve el entorno WSGI modificado para incluir el flujo de entrada HTTP.
        """
        environ = self.request.httprequest.environ
        environ["wsgi.input"] = self.request.httprequest._get_stream_for_parsing()
        return environ

    @contextmanager
    def _manage_odoo_env(self, uid=None):
        """
        Administra el entorno de Odoo con un UID opcional y contexto FastAPI.
        """
        env = self.request.env
        if uid:
            env = env(user=uid)

        token = odoo_env_ctx.set(env)
        try:
            yield
        finally:
            odoo_env_ctx.reset(token)


class IrHttp(models.AbstractModel):
    """
    Modelo heredado de `ir.http` para integrar enrutamiento con FastAPI.
    """
    _inherit = "ir.http"

    def _generate_routing_rules(cls, modules, converters):
        """
        Genera reglas de enrutamiento combinando las reglas originales con las de FastAPI.
        """
        return chain(
            super()._generate_routing_rules(modules, converters),
            cls._endpoint_routing_rules(),
        )

    def _endpoint_routing_rules(cls):
        """
        Define las reglas de enrutamiento específicas para los endpoints de FastAPI.
        """
        from ..fastapi import odoo_routes  # Importar odoo_routes dentro de la función

        method = getattr(FastApiDispatcher(odoo_request), "dispatch")
        endpoint = partial(method, (), {})
        update_wrapper(endpoint, method)
        endpoint.routing = get_routing()

        for route in odoo_routes:
            yield (route, endpoint)

