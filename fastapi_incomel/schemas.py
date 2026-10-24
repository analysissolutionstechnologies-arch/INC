# # -*- coding:utf-8 -*-
#
# import inspect
# from typing import Any, Dict, List, Optional, Union
#
# from dotty_dict import dotty
# from odoo import fields, models
# from pydantic import BaseModel, ConfigDict, RootModel, model_validator
#
#
# class Token(BaseModel):
#     access_token: str
#     refresh_token: str
#     expires_in: int
#     token_type: str
#
#
# class TokenData(BaseModel):
#     login: Union[str, None] = None
#
#
# class ChangePassword(BaseModel):
#     old_password: str
#     new_password: str
#     confirm_password: str
#
#
# class RecordParams(BaseModel):
#     model: str
#     context: Optional[dict] = {}
#
#
# class CreateParams(RecordParams):
#     vals: dict
#     fields: Optional[str] = None
#
#
# class CreateMultiParams(RecordParams):
#     vals_list: List[dict]
#     fields: Optional[str] = None
#
#
# class UpdateParams(RecordParams):
#     ids: Union[int,List[int]]
#     vals: dict
#     fields: Optional[str] = None
#
#
# class DeleteParams(RecordParams):
#     ids: Union[int,List[int]]
#
#
# class MethodParams(RecordParams):
#     method: str
#     ids: Optional[Union[int,List[int]]] = None
#     fields: Optional[str] = None
#     args: Optional[list] = []
#     kwargs: Optional[dict] = {}
#
#
# class ResponseModel(BaseModel):
#     success: bool
#     error: Optional[str] = None
#     user: Optional[dict] = {}
#     result: Any
#     records: Optional[Any] = None
#
#
# class ResponseModels(BaseModel):
#     success: bool
#     total: int
#     error: Optional[str] = None
#     user: Optional[dict] = {}
#     result: Any
#
#
# class OdooModel(RootModel):
#     model_config = ConfigDict(from_attributes=True)
#     root: Dict[str, Any]
#
#     def __getitem__(self, key):
#         return self.root(key)
#
#     @model_validator(mode="before")
#     @classmethod
#     def validate(cls, record, values):
#         dot_fields = dotty()
#         for field in values.context.get("fields"):
#             dot_fields[field] = None
#
#         res = cls.process_fields(record, dot_fields.to_dict())
#         return res
#
#     def get(record, key: Any, default: Any = None) -> Any:
#         res = getattr(record, key, default)
#         if isinstance(record, models.BaseModel) and key in record._fields:
#             field = record._fields[key]
#             if res is False and field.type != "boolean":
#                 return None
#             if field.type == "date" and not res:
#                 return None
#             if field.type == "datetime":
#                 if not res:
#                     return None
#                 return fields.Datetime.context_timestamp(record, res)
#             if field.type == "many2one":
#                 if not res:
#                     return None
#                 return {"id": res.id, "display_name": res.display_name}
#             if field.type == "binary":
#                 if not res or not field.attachment:
#                     return None
#                 attach = record.get_field_binary(field.name)
#                 if not attach:
#                     return None
#                 base_url = record.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
#                 return {
#                     "file_path": (
#                         base_url
#                         + "/api/v1/file?token="
#                         + attach[0]
#                         if attach[1]
#                         not in [
#                             "application/octet-stream",
#                             "video/mp4",
#                             "video/3gpp",
#                         ]
#                         else
#                         base_url
#                         + "/api/v1/video?token="
#                         + attach[0]
#                     ),
#                     "mimetype": attach[1],
#                 }
#             if field.type == "selection":
#                 if not res:
#                     return None
#                 options = dict(field.get_description(record.env)["selection"])
#                 return {"value": res, "label": options.get(record[key])}
#             if field.type in ["one2many", "many2many"]:
#                 if not res:
#                     return None
#                 else:
#                     return [{"id": r.id, "display_name": r.display_name} for r in res]
#         elif inspect.ismethod(getattr(record, key)):
#             return getattr(record, key)()
#         return res
#
#     @classmethod
#     def process_fields(cls, record, fields={}):
#         res = {}
#         for key, value in fields.items():
#             if value is None:
#                 res[key] = cls.get(record, key=key)
#                 continue
#
#             nested_record = getattr(record, key, None)
#             if not isinstance(nested_record, models.BaseModel):
#                 res[key] = None
#                 continue
#
#             field = record._fields[key]
#             if field.type == "many2one":
#                 res[key] = cls.process_fields(nested_record, value)
#             elif field.type in ["one2many", "many2many"]:
#                 if not nested_record:
#                     res[key] = None
#                     continue
#
#                 res[key] = [
#                     cls.process_fields(record, value) for record in nested_record
#                 ]
#         return res


# -*- coding:utf-8 -*-
import inspect
from typing import Any, Dict, List, Optional, Union

from dotty_dict import dotty
from odoo import fields, models
from pydantic import BaseModel, ConfigDict, RootModel, model_validator


############### Modelos para la API ###############

class Token(BaseModel):
    """Modelo para los datos del token de autenticación."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


class TokenData(BaseModel):
    """Modelo para los datos asociados al token."""
    login: Optional[str] = None


class ChangePassword(BaseModel):
    """Modelo para cambiar contraseñas."""
    old_password: str
    new_password: str
    confirm_password: str


############### Modelos para Parámetros ###############

class RecordParams(BaseModel):
    """Parámetros base para interacciones con modelos Odoo."""
    model: str
    context: Optional[dict] = {}


class CreateParams(RecordParams):
    """Parámetros para la creación de registros."""
    vals: dict
    fields: Optional[str] = None


class CreateMultiParams(RecordParams):
    """Parámetros para la creación de múltiples registros."""
    vals_list: List[dict]
    fields: Optional[str] = None


class UpdateParams(RecordParams):
    """Parámetros para la actualización de registros."""
    ids: Union[int, List[int]]
    vals: dict
    fields: Optional[str] = None


class DeleteParams(RecordParams):
    """Parámetros para la eliminación de registros."""
    ids: Union[int, List[int]]


class MethodParams(RecordParams):
    """Parámetros para llamar métodos en modelos Odoo."""
    method: str
    ids: Optional[Union[int, List[int]]] = None
    fields: Optional[str] = None
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}


############### Modelos para Respuestas ###############

class ResponseModel(BaseModel):
    """Modelo de respuesta para operaciones individuales."""
    success: bool
    error: Optional[str] = None
    user: Optional[dict] = {}
    result: Any
    records: Optional[Any] = None


class ResponseModels(BaseModel):
    """Modelo de respuesta para operaciones múltiples."""
    success: bool
    total: int
    error: Optional[str] = None
    user: Optional[dict] = {}
    result: Any


############### Modelo de Validación para Odoo ###############

class OdooModel(RootModel):
    """
    Modelo para validar y estructurar datos de registros Odoo.
    """
    model_config = ConfigDict(from_attributes=True)
    root: Dict[str, Any]

    def __getitem__(self, key):
        return self.root.get(key)

    @model_validator(mode="before")
    @classmethod
    def validate(cls, record, values):
        """
        Valida y transforma los campos antes de procesarlos.
        """
        dot_fields = dotty()
        for field in values.get("context", {}).get("fields", []):
            dot_fields[field] = None

        return cls.process_fields(record, dot_fields.to_dict())

    @staticmethod
    def get(record, key: Any, default: Any = None) -> Any:
        """
        Obtiene el valor de un campo en un registro Odoo.
        """
        res = getattr(record, key, default)
        if isinstance(record, models.BaseModel) and key in record._fields:
            field = record._fields[key]

            if not res and field.type not in ["boolean", "many2one"]:
                return None

            if field.type == "date" and not res:
                return None

            if field.type == "datetime":
                return fields.Datetime.context_timestamp(record, res) if res else None

            if field.type == "many2one":
                return {"id": res.id, "display_name": res.display_name} if res else None

            if field.type == "binary" and res and field.attachment:
                attach = record.get_field_binary(field.name)
                if attach:
                    base_url = record.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
                    file_type = "video" if attach[1] in ["video/mp4", "video/3gpp"] else "file"
                    return {
                        "file_path": f"{base_url}/api/v1/{file_type}?token={attach[0]}",
                        "mimetype": attach[1],
                    }

            if field.type == "selection" and res:
                options = dict(field.get_description(record.env)["selection"])
                return {"value": res, "label": options.get(res)}

            if field.type in ["one2many", "many2many"]:
                return [{"id": r.id, "display_name": r.display_name} for r in res] if res else None

        elif inspect.ismethod(getattr(record, key, None)):
            return getattr(record, key)()

        return res

    @classmethod
    def process_fields(cls, record, fields: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Procesa los campos anidados para construir un diccionario.
        """
        res = {}
        for key, value in fields.items():
            if value is None:
                res[key] = cls.get(record, key)
                continue

            nested_record = getattr(record, key, None)
            if isinstance(nested_record, models.BaseModel):
                field = record._fields[key]
                if field.type == "many2one":
                    res[key] = cls.process_fields(nested_record, value)
                elif field.type in ["one2many", "many2many"]:
                    res[key] = [
                        cls.process_fields(nr, value) for nr in nested_record
                    ] if nested_record else None
            else:
                res[key] = None
        return res
