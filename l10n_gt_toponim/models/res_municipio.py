#


from odoo import api, fields, models, _
import pandas as pd
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime
import requests
import base64, json
from io import BytesIO
 

class Estado(models.Model):
    _inherit = "res.country.state"

    
    id_region = fields.Char(string="Id Region")
    id_tipo_region = fields.Char(string="Id Tipo Region")
    id_pais = fields.Char(string="Id Pais")
    cmp_nombre_region = fields.Char(string="Cmp Nombre Region" , unique=True)
    cmp_fecha_ingreso_region = fields.Char(string="Cmp Fecha Ingreso Region")
    id_regional = fields.Char(string="Id Regional")
    cmp_codigo_region = fields.Char(string="Cmp Codigo Region")
    cmp_activo = fields.Char(string="Cmp Activo")
    cmp_codigo_odm = fields.Char(string="Cmp Codigo Odm")





class Resmunicipio(models.Model):

    _name = "res.municipiogt"

    name = fields.Char(string="Municipio" , unique=True)
    code = fields.Char(string="Codigo" , unique=True)
    ID_CIUDAD = fields.Integer()
    ID_REGION = fields.Integer()
    CMP_NOMBRE_CIUDAD = fields.Char()
    CMP_FECHA_INGRESO_CIUDAD = fields.Char()
    Cmp_Codigo_Renap = fields.Char()
    CMP_CODIGO_EvaSmart = fields.Char()
    CMP_ESTADO = fields.Char()
    Cmp_Activo = fields.Char()
    # ID_CIUDAD	ID_REGION	CMP_NOMBRE_CIUDAD	CMP_FECHA_INGRESO_CIUDAD	Cmp_Codigo_Renap	CMP_CODIGO_EvaSmart	CMP_ESTADO	Cmp_Activo



    state_id = fields.Many2one( 'res.country.state',string="Departamento" , domain="[('country_id.code', '=', 'GT')]" )
    charge_data_excel = fields.Boolean()
    data_binary = fields.Binary()


    archivo_data = fields.Binary(
        string='Archivo EXCEL',
    )
    

    def cargar_estados(self , df, sheet_name):
        for rec in self:
            cantidad = 0
            lista_data = []
            for index, row in df.iterrows():
                    cantidad += 1
                    print("ROW: ",row.iloc[0])
                    print("ROW: ",row.iloc[0] in ['', None, 'nan', 0, '0' ])
                    if  row.iloc[0]  in ['', None, 'nan', 0, '0' ]:
                        continue
                    
                    # Imprimir la línea completa del DataFrame
                    print("AGREGAR!!!!!: ",row.iloc[0])
                    lista_data.append( row.to_dict())
            print("LISTA DATA: ",lista_data)
            print("!!!")
            ids_creados = []
            for data in lista_data:
                
                print("DATA: ",data)
# LISTA DATA:  [{'ID_REGION': 0, 'ID_TIPO_REGION': 2, 'ID_PAIS': 83, 'CMP_NOMBRE_REGION': ' SIN DEPARTAMENTO', 'CMP_FECHA_INGRESO_REGION': Timestamp('2009-06-23 10:29:00.967000'), 'ID_REGIONAL': 0, 'CMP_CODIGO_REGION': nan, 'Cmp_Activo': 1, 'CMP_CODIGO_ODM': nan}]

                id_region = int(data['ID_REGION'])
                id_tipo_region = int(data['ID_TIPO_REGION'])
                id_pais = int(data['ID_PAIS'])
                cmp_nombre_region = data['CMP_NOMBRE_REGION']
                cmp_fecha_ingreso_region = data['CMP_FECHA_INGRESO_REGION']
                id_regional = int(data['ID_REGIONAL'])
                cmp_codigo_region = data['CMP_CODIGO_REGION']
                cmp_activo = data['Cmp_Activo']
                cmp_codigo_odm = data['CMP_CODIGO_ODM']



                dict_data = {
                    'id_region': id_region,
                    'id_tipo_region': id_tipo_region,
                    'id_pais': id_pais,
                    'cmp_nombre_region': cmp_nombre_region,
                    'cmp_fecha_ingreso_region': cmp_fecha_ingreso_region,
                    'id_regional': id_regional,
                    'cmp_codigo_region': cmp_codigo_region,
                    'cmp_activo': cmp_activo,
                    'cmp_codigo_odm': cmp_codigo_odm
                }
                print("DICT DATA: ",dict_data)
                search_state = self.env['res.country.state'].search([('name', '=', cmp_nombre_region)])
                if not search_state:
                    search_state = self.env['res.country.state'].search([('cmp_nombre_region', '=', cmp_nombre_region)])
                                                                        
                if not search_state:
                    search_state = self.env['res.country.state'].search([('name', 'ilike', cmp_nombre_region.lower()) , 
                                                                        ('id_region', '=', False)])

                if not search_state:
                    dict_data['name'] = cmp_nombre_region 
                    dict_data['code'] = cmp_codigo_region 
                    dict_data['country_id'] = self.env['res.country'].search([('code', '=', 'GT')]).id
                    estado_id = self.env['res.country.state'].create(dict_data)
                else:
                    estado_id = search_state
                    estado_id.write(dict_data)
                ids_creados.append(estado_id)
            return lista_data
            


    def cargar_municipios_ciudades(self , df, sheet_name):
        for rec in self:
            cantidad = 0
            lista_data = []
            for index, row in df.iterrows():
                    cantidad += 1
                    if  row.iloc[0]  in ['', None, 'nan', 0, '0' ]:
                        continue
                    
                    # Imprimir la línea completa del DataFrame
                    lista_data.append( row.to_dict())
            ids_creados = []
            for data in lista_data:
                
    # ID_CIUDAD	ID_REGION	CMP_NOMBRE_CIUDAD	CMP_FECHA_INGRESO_CIUDAD	Cmp_Codigo_Renap	CMP_CODIGO_EvaSmart	CMP_ESTADO	Cmp_Activo

                ID_CIUDAD = int(data['ID_CIUDAD'])
                ID_REGION = int(data['ID_REGION'])
                CMP_NOMBRE_CIUDAD = data['CMP_NOMBRE_CIUDAD']
                CMP_FECHA_INGRESO_CIUDAD = data['CMP_FECHA_INGRESO_CIUDAD']
                Cmp_Codigo_Renap = data['Cmp_Codigo_Renap']
                CMP_CODIGO_EvaSmart = data['CMP_CODIGO_EvaSmart']
                CMP_ESTADO = data['CMP_ESTADO']
                Cmp_Activo = data['Cmp_Activo']



                dict_data = {
                    'ID_CIUDAD': ID_CIUDAD,
                    'ID_REGION': ID_REGION,
                    'CMP_NOMBRE_CIUDAD': CMP_NOMBRE_CIUDAD,
                    'CMP_FECHA_INGRESO_CIUDAD': CMP_FECHA_INGRESO_CIUDAD,
                    'Cmp_Codigo_Renap': Cmp_Codigo_Renap,
                    'CMP_CODIGO_EvaSmart': CMP_CODIGO_EvaSmart,
                    'CMP_ESTADO': CMP_ESTADO,
                    'Cmp_Activo': Cmp_Activo,
                    'code': ID_CIUDAD,
                }
                print("DICT DATA: ",dict_data)
                search_state = self.env['res.municipiogt'].search([('name', '=', CMP_NOMBRE_CIUDAD)])
                if not search_state:
                    search_state = self.env['res.municipiogt'].search([('CMP_NOMBRE_CIUDAD', '=', CMP_NOMBRE_CIUDAD)])
                                                                        
                if not search_state:
                    search_state = self.env['res.municipiogt'].search([('name', 'ilike', CMP_NOMBRE_CIUDAD.lower()) , 
                                                                        ('ID_CIUDAD', '=', False)])

                if not search_state:
                    dict_data['name'] = CMP_NOMBRE_CIUDAD 
                    dict_data['code'] = Cmp_Codigo_Renap 
                    state_id = self.env['res.country.state'].search([('id_region', '=', ID_REGION)])
                    dict_data['state_id'] = state_id.id 

                    # dict_data['country_id'] = self.env['res.country'].search([('code', '=', 'GT')]).id
                    municipio_id = self.env['res.municipiogt'].create(dict_data)
                else:
                    municipio_id = search_state
                    municipio_id.write(dict_data)
                ids_creados.append(municipio_id)
            return ids_creados
            


    def cargar_sector_municipios(self , df, sheet_name):
        for rec in self:
            cantidad = 0
            lista_data = []
            for index, row in df.iterrows():
                    cantidad += 1
                    if  row.iloc[0]  in ['', None, 'nan', 0, '0' ]:
                        continue
                    
                    # Imprimir la línea completa del DataFrame
                    lista_data.append( row.to_dict())
            ids_creados = []
            for data in lista_data:
                
# ID_SECTOR	ID_ZONA	ID_TIPO_SECTOR	ID_CIUDAD	CMP_NOMBRE_SECTOR	CMP_FECHA_INGRESO_SECTOR	CMP_ESTADO_SECTOR	Cmp_Activo
                if data['Cmp_Activo'] in ['', None, 'nan', 0, '0' , False]:
                    print("Cmp_Activo: ",data['Cmp_Activo'] , "NO ACTIVO")
                    continue
                if data['ID_CIUDAD'] in ['', None, 'nan', 0, '0' , False]:
                    print("ID_CIUDAD: ",data['ID_CIUDAD'] , "NO ACTIVO")
                    continue
                
                print("DATA: ",data)

                print("data['ID_CIUDAD']: ",data['ID_CIUDAD'])
                ID_SECTOR = int(data['ID_SECTOR'] )
                ID_SECTOR = int( ID_SECTOR )
                ID_ZONA = int(data['ID_ZONA'])
                ID_TIPO_SECTOR = int(data['ID_TIPO_SECTOR'])
                ID_CIUDAD = int(data['ID_CIUDAD'])
                CMP_NOMBRE_SECTOR = data['CMP_NOMBRE_SECTOR']
                CMP_FECHA_INGRESO_SECTOR = data['CMP_FECHA_INGRESO_SECTOR']
                CMP_ESTADO_SECTOR = data['CMP_ESTADO_SECTOR']
                Cmp_Activo = data['Cmp_Activo']



                dict_data = { 
                    'ID_SECTOR': ID_SECTOR,
                    'ID_ZONA': ID_ZONA,
                    'ID_TIPO_SECTOR': ID_TIPO_SECTOR,
                    'ID_CIUDAD': ID_CIUDAD,
                    'CMP_NOMBRE_SECTOR': CMP_NOMBRE_SECTOR,
                    'CMP_FECHA_INGRESO_SECTOR': CMP_FECHA_INGRESO_SECTOR,
                    'CMP_ESTADO_SECTOR': CMP_ESTADO_SECTOR,
                    'Cmp_Activo': Cmp_Activo
                }
                search_zona = self.env['res.zonagt'].search([('name', '=', CMP_NOMBRE_SECTOR),
                                                            ('ID_SECTOR', '=', ID_SECTOR)])
                if not search_zona:
                    search_zona = self.env['res.zonagt'].search([('CMP_NOMBRE_SECTOR', '=', CMP_NOMBRE_SECTOR),
                                                            ('ID_SECTOR', '=', ID_SECTOR) ])
                                                                        
                if not search_zona:
                    search_zona = self.env['res.zonagt'].search([('name', 'ilike', CMP_NOMBRE_SECTOR.lower() ),
                                                            ('ID_SECTOR', '=', ID_SECTOR),
                                                            ('ID_ZONA', '=', False)])

                if not search_zona:
                    municipio_id = self.env['res.municipiogt'].search([('ID_CIUDAD', '=', ID_CIUDAD)])
                    dict_data['municipio_id'] = municipio_id.id 

                    dict_data['name'] = CMP_NOMBRE_SECTOR 
                    dict_data['code'] = int( ID_SECTOR ) #ID_SECTOR 
                    # dict_data['country_id'] = self.env['res.country'].search([('code', '=', 'GT')]).id
                    zona_id = self.env['res.zonagt'].create(dict_data)
                else:
                    zona_id = search_zona
                    zona_id.write(dict_data)
                ids_creados.append(zona_id)
            return ids_creados
            


    def cargar_colonia_sectores(self , df, sheet_name):
        for rec in self:
            cantidad = 0
            lista_data = []
            for index, row in df.iterrows():
                    cantidad += 1
                    if  row.iloc[0]  in ['', None, 'nan', 0, '0' ]:
                        continue
                    
                    # Imprimir la línea completa del DataFrame
                    lista_data.append( row.to_dict())
            ids_creados = []
            for data in lista_data:
              
# ID_BARRIO	ID_PAIS	ID_REGION	ID_CIUDAD	ID_SECTOR	CMP_DESCRIPCION_BARRIO	CMP_FECHA_INGRESO	Cmp_Activo
                if data['Cmp_Activo'] in ['', None, 'nan', 0, '0' , False]:
                    print("Cmp_Activo: ",data['Cmp_Activo'] , "NO ACTIVO")
                    continue
                if data['ID_CIUDAD'] in ['', None, 'nan', 0, '0' , False]:
                    print("ID_CIUDAD: ",data['ID_CIUDAD'] , "NO ACTIVO")
                    continue
                ID_BARRIO = int(data['ID_BARRIO'])
                ID_PAIS = int(data['ID_PAIS'])
                ID_REGION = int(data['ID_REGION'])
                ID_CIUDAD = int(data['ID_CIUDAD'])
                ID_SECTOR = int(data['ID_SECTOR'])
                CMP_DESCRIPCION_BARRIO = data['CMP_DESCRIPCION_BARRIO']
                CMP_FECHA_INGRESO = data['CMP_FECHA_INGRESO']
                Cmp_Activo = data['Cmp_Activo']

                dict_data = { 
                    'ID_BARRIO': ID_BARRIO,
                    'ID_PAIS': ID_PAIS,
                    'ID_REGION': ID_REGION,
                    'ID_CIUDAD': ID_CIUDAD,
                    'ID_SECTOR': ID_SECTOR,
                    'CMP_DESCRIPCION_BARRIO': CMP_DESCRIPCION_BARRIO,
                    'CMP_FECHA_INGRESO': CMP_FECHA_INGRESO,
                    'Cmp_Activo': Cmp_Activo
                }
                search_colonia = self.env['res.coloniagt'].search([('name', '=', CMP_DESCRIPCION_BARRIO),
                                                                    ('ID_BARRIO', '=', ID_BARRIO)])
                if not search_colonia:
                    search_colonia = self.env['res.coloniagt'].search([('CMP_DESCRIPCION_BARRIO', '=', CMP_DESCRIPCION_BARRIO ) ,
                                                                        ('ID_BARRIO', '=', ID_BARRIO) ])
                                                                        
                if not search_colonia:
                    search_colonia = self.env['res.coloniagt'].search([('name', 'ilike', CMP_DESCRIPCION_BARRIO) 
                                                                   , ('ID_BARRIO', '=', ID_BARRIO), 
                                                                    ])
                                                                #    ('ID_CIUDAD', '=', False)])

                if not search_colonia:
                    dict_data['name'] = CMP_DESCRIPCION_BARRIO 
                    dict_data['code'] = ID_BARRIO 
                    print("ID_CIUDAD", ID_CIUDAD)
                    municipio_id = self.env['res.municipiogt'].search([('ID_CIUDAD', '=', ID_CIUDAD) ])
                    zona_id = self.env['res.zonagt'].search([('ID_SECTOR', '=', ID_SECTOR)])
                    if len(municipio_id) > 1 :
                        for municipio in municipio_id:
                            print("municipio", municipio.name)
                            print("ID_CIUDAD", municipio.ID_CIUDAD)
                    dict_data['municipio_id'] = municipio_id.id 
                    dict_data['zona_id'] = zona_id.id 

                    # dict_data['country_id'] = self.env['res.country'].search([('code', '=', 'GT')]).id
                    colonia_id = self.env['res.coloniagt'].create(dict_data)
                else:
                    colonia_id = search_colonia
                    colonia_id.write(dict_data)
                ids_creados.append(colonia_id)
            return ids_creados
            



    def cargar_data_excel(self):
        for rec in self:
            print("REC")
            file = rec.archivo_data
            if not file:
                raise UserError(_('Por favor agregue un Archivo'))
            
            # Decodificar el archivo binario
            file_data = base64.b64decode(file)
            
            # Leer el archivo Excel usando pandas con BytesIO
            try:
                # Leer todas las hojas del archivo Excel
                xls = pd.ExcelFile(BytesIO(file_data))
                sheet_names = xls.sheet_names
            except Exception as e:
                raise UserError(_('Error al leer el archivo Excel: %s') % str(e))
            
            lista_data = []
            for sheet_name in sheet_names:
                
                try:
                    df = pd.read_excel(BytesIO(file_data), sheet_name=sheet_name)
                except Exception as e:
                    raise UserError(_('Error al leer la hoja "%s" del archivo Excel: %s') % (sheet_name, str(e)))
                
                cantidad = 0
                print("Hoja:", sheet_name)
                if sheet_name.lower() == 'estado' or 'estado' in sheet_name.lower():
                    estados = self.cargar_estados( df  , sheet_name)
                    print("fin" , estados)
                    
                    pass
                elif sheet_name.lower() == 'municipio' or 'municipio' in sheet_name.lower():
                    municipios = self.cargar_municipios_ciudades( df  , sheet_name)
                    print("fin" , municipios)

                    pass
                if sheet_name.lower() == 'zona' or 'zona' in sheet_name.lower():
                    zonas = self.cargar_sector_municipios( df  , sheet_name)
                    print("fin cargar_sector_municipios")

                    pass
                if sheet_name.lower() == 'colonia' or 'colonia' in sheet_name.lower():
                    colonias = self.cargar_colonia_sectores( df  , sheet_name)
                    print("fin cargar_colonias")

                    pass
                
            
            # Aquí puedes hacer lo que necesites con la lista_data
            print("Lista de datos:", lista_data)
            
