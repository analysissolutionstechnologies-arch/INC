# Widget IFrame URL para Odoo 17

## Descripción
Este módulo añade un widget personalizado llamado `iframe_url` que permite mostrar campos de tipo texto como iframes en las vistas de formulario de Odoo 17.

## Instalación

1. Copia la carpeta `iframe_widget` en tu directorio de addons de Odoo
2. Actualiza la lista de aplicaciones en Odoo
3. Instala el módulo "Widget IFrame URL"

## Uso

### En tu modelo Python:

```python
from odoo import models, fields

class MiModelo(models.Model):
    _name = 'mi.modelo'
    _description = 'Mi Modelo'
    
    view_external_url_text = fields.Char(
        string='URL Externa',
        help='URL que se mostrará en el iframe'
    )
```

### En tu vista XML:

```xml
<record id="view_mi_modelo_form" model="ir.ui.view">
    <field name="name">mi.modelo.form</field>
    <field name="model">mi.modelo</field>
    <field name="arch" type="xml">
        <form>
            <sheet>
                <group>
                    <field name="view_external_url_text" widget="iframe_url"/>
                </group>
            </sheet>
        </form>
    </field>
</record>
```

## Características

- **Altura configurable**: El iframe tiene una altura predeterminada de 600px
- **Ancho responsive**: El iframe ocupa el 100% del ancho disponible
- **Sin bordes**: frameborder="0" para una apariencia limpia
- **Validación**: Si el campo está vacío, muestra un mensaje indicativo
- **Estilo**: Incluye un borde sutil y esquinas redondeadas

## Personalización

Si deseas modificar las dimensiones del iframe, puedes editar el archivo:
`iframe_widget/static/src/xml/iframe_url_widget.xml`

Y cambiar los valores de `width` y `height` según tus necesidades.

## Requisitos

- Odoo 17.0
- Módulo `web` (incluido por defecto en Odoo)

## Licencia

LGPL-3
