# INCOMEL - Menú de aplicaciones para Odoo Community 19

Implementación independiente, LGPL-3. No contiene código ni recursos de Odoo Enterprise ni requiere MuK.

## Instalación
1. Desinstala el tema anterior INCOMEL o MuK que modifique el menú; pueden competir por la misma vista. Hazlo primero en pruebas.
2. Descomprime el ZIP. Copia la carpeta `incmd_app_launcher` completa a un directorio incluido en `addons_path`. El archivo `__manifest__.py` debe estar directamente dentro de esa carpeta, sin otra carpeta intermedia.
3. Reinicia el servicio/contenedor de Odoo.
4. Activa el modo desarrollador. En Aplicaciones, selecciona Actualizar lista de aplicaciones.
5. Busca `INCOMEL - Menu de aplicaciones` e instala. Si no aparece, quita el filtro Aplicaciones y busca `incmd_app_launcher`.
6. Recarga con Ctrl+Shift+R (Mac: Cmd+Shift+R).

No hay configuración adicional ni dependencias pip. Depende únicamente de `web`.

## Funcionamiento
El botón de cuadrícula en la esquina superior izquierda abre el inicio de aplicaciones. Al entrar por /odoo o /web sin una acción explícita se abre automáticamente. Los enlaces directos a pantallas específicas conservan su navegación. Escape o X cierra el inicio y permite regresar a la pantalla anterior. Al elegir una aplicación se utiliza el servicio nativo de menús de Odoo; los submenús y permisos conservan su comportamiento original. Solo muestra aplicaciones que el usuario puede ver.

Usa los iconos de las aplicaciones instaladas. Si una aplicación no tiene icono, muestra su inicial. No instala aplicaciones de Enterprise.

## Actualizar por consola
Con el servicio detenido y usando el mismo usuario/configuración que la instancia:

    odoo -c /ruta/odoo.conf -d NOMBRE_BASE -u incmd_app_launcher --stop-after-init

Para primera instalación sustituye `-u` por `-i`. El ejecutable puede llamarse `odoo-bin` según tu instalación. Luego inicia nuevamente Odoo.

## Desinstalación
Desinstala desde Aplicaciones. No borres la carpeta antes de desinstalar. Recarga el navegador.

## Validación
Revisado contra la estructura de NavBar de Odoo 19.0 Community. Verificación estática de manifiesto, XML, XPath y sintaxis JavaScript. No se ha instalado en una instancia real; probar en staging antes de producción. No se declara compatibilidad con 17/18 ni con otros temas de backend.

## Cambio 19.0.1.0.1
En la cuadrícula se ocultan el nombre de la aplicación anterior, sus submenús y las migas de navegación de la barra. Se conservan el botón de aplicaciones y los controles globales (mensajes, actividades y usuario). Al abrir una aplicación o cerrar la cuadrícula se restaura su navegación. En móvil el menú lateral solo aparece dentro de una aplicación.

Para actualizar: sustituye la carpeta incmd_app_launcher, reinicia Odoo, actualiza el módulo desde Aplicaciones y recarga con Ctrl+Shift+R. No hace falta desinstalar este módulo.

## Cambio 19.0.1.0.2
Se oculta el botón superior izquierdo de cuadrícula mientras el inicio de aplicaciones está abierto. Al entrar en una aplicación vuelve a aparecer para permitir regresar al inicio. Se mantienen los ajustes anteriores de ocultación de submenús.

## Cambio 19.0.1.0.3
Dentro de cada aplicación se muestra su icono y nombre en la esquina superior izquierda, sin duplicar el nombre nativo. Pulsar ese encabezado abre el inicio de aplicaciones. Los submenús nativos continúan a su derecha. En la pantalla de cuadrícula el encabezado sigue oculto. Los módulos sin icono usan su inicial.

## Cambio 19.0.1.0.4
Se retiran el título Aplicaciones y el buscador del inicio. Se conservan la cuadrícula, el botón de cierre y los ajustes de navegación anteriores.

## Cambio 19.0.1.0.5
Se elimina también la X de cierre y su fila vacía. El inicio muestra únicamente la cuadrícula. Se ingresa pulsando una aplicación; Escape conserva el regreso a la pantalla anterior.
