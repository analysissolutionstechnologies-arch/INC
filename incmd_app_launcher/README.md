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
El botón de cuadrícula en la esquina superior izquierda abre el inicio de aplicaciones. Al entrar por /odoo o /web sin una acción explícita se abre automáticamente. Los enlaces directos a pantallas específicas conservan su navegación. El buscador ignora tildes y mayúsculas. Escape o X cierra el inicio y permite regresar a la pantalla anterior. Al elegir una aplicación se utiliza el servicio nativo de menús de Odoo; los submenús y permisos conservan su comportamiento original. Solo muestra aplicaciones que el usuario puede ver.

Usa los iconos de las aplicaciones instaladas. Si una aplicación no tiene icono, muestra su inicial. No instala aplicaciones de Enterprise.

## Actualizar por consola
Con el servicio detenido y usando el mismo usuario/configuración que la instancia:

    odoo -c /ruta/odoo.conf -d NOMBRE_BASE -u incmd_app_launcher --stop-after-init

Para primera instalación sustituye `-u` por `-i`. El ejecutable puede llamarse `odoo-bin` según tu instalación. Luego inicia nuevamente Odoo.

## Desinstalación
Desinstala desde Aplicaciones. No borres la carpeta antes de desinstalar. Recarga el navegador.

## Validación
Revisado contra la estructura de NavBar de Odoo 19.0 Community. Verificación estática de manifiesto, XML, XPath y sintaxis JavaScript. No se ha instalado en una instancia real; probar en staging antes de producción. No se declara compatibilidad con 17/18 ni con otros temas de backend.
