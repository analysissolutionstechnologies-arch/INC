# INCOMEL Backblaze Storage — Odoo 17

Paquete nuevo: incmd_b2_storage. No es actualización directa de incmd_attachment_b2. No instalar ambos interceptores de almacenamiento juntos. Antes de sustituir el anterior hay que adaptar sus referencias b2://; este paquete utiliza b2v2://. No desinstalar el módulo que permite leer adjuntos remotos existentes.

## Instalación
Instalar requirements.txt con el Python del servidor, copiar incmd_b2_storage al addons_path, actualizar aplicaciones e instalar en QA. En Odoo.sh agregar boto3>=1.34,<2 al requirements.txt de la raíz del repositorio. Ubuntu 22.04/24.04: usar el Python y dependencias requeridos por la versión de Odoo. No hay dependencia de comandos propios de Ubuntu.

## Configuración
Menú Backblaze (administradores): crear repositorio S3 privado, endpoint, región, bucket, Application Key ID y Application Key con permisos de lectura/escritura. Probar conexión. Crear reglas: seleccionar módulo opcional y modelo concreto, MIME separados por coma (admite image/*), extensiones y campos binarios de negocio opcionales. Las reglas son por modelo; para cubrir un módulo crear sus reglas por modelo. Los archivos técnicos y modelos ir.*, web.*, bus.*, base.* están excluidos. Archivos sin registro relacionado permanecen locales. Los campos binarios solo se envían si se enumeran explícitamente. No seleccionar campos de logos/iconos/interfaz.

Las cargas se guardan primero con Odoo y luego se transfieren. Ante fallo permanecen locales con reintento en 15 minutos. Activar la acción planificada Backblaze: sincronización y migración (se entrega desactivada). Habilitar Migración histórica en el repositorio para recorrer históricos en lotes. Ejecutar lote también permite prueba manual. Reiniciar recorrido en reglas para reconsiderar históricos tras cambiar filtros. Tamaño máximo por archivo 50 MB por defecto; los mayores permanecen locales.

## Hash y liberación local
Claves SHA-256 por contenido dentro del prefijo y bucket. Comprueba existencia, reutiliza sin PUT si ya existe, descarga y verifica SHA-256/SHA-1/tamaño. Conserva nombre original en Odoo. La limpieza se ejecuta después del commit en una transacción independiente, bajo bloqueo de tabla y solo si no quedan referencias locales. Local Released indica liberado/no requerido; falso puede significar archivo compartido o limpieza pendiente. Se reintenta en el siguiente lote. Serialización de contenido idéntico dentro de esta base; no coordina distintas bases Odoo que escriban simultáneamente al mismo bucket. No convierte automáticamente objetos remotos con claves aleatorias de versiones previas; esos siguen siendo legibles.

## Integridad y acceso
Se conserva ID, res_model, res_id, res_field, checksum y permisos originales. Historial guarda relación, ruta anterior y destino. Verifica SHA1 local y descarga remota antes de cambiar store_fname. La liberación física local se realiza después del commit; GC nativo sigue disponible como limpieza complementaria. No se borran objetos remotos al eliminar adjuntos: se conservan para evitar pérdida por rollback o referencias compartidas. No incluye purga remota automática. Credenciales solo accesibles a administradores; proteger backups de la BD.

Se usa API S3 con firma SigV4 nueva en cada solicitud; no guarda URLs ni tokens de descarga que expiren. Ante ExpiredToken/InvalidToken/RequestExpired reconstruye cliente y reintenta una vez. Application Keys revocadas requieren actualizar configuración. Los documentos se sirven a través de Odoo y sus permisos, sin enlaces públicos. No hay copia local permanente tras migración ni descarga disponible si Backblaze cae. Las lecturas remotas y verificación usan memoria; limitar tamaño y lote según RAM/carga.

## Validación pendiente en servidor
Validaciones estáticas incluidas; no se ejecutó instalación real en Odoo ni pruebas contra su bucket. Probar en QA: instalación, vistas, conexión, carga/descarga de PDF e imagen, permisos con usuario de tienda, fallo de conexión/carga local, cron/reintento, migración, edición de archivo, copia de registro, documentos compartidos, reportes y archivos técnicos. Realizar respaldo antes de migrar. Nunca desinstalar con adjuntos remotos: primero repatriar o mantener lector.

## Versión 27: documentos de la cotización
En Ventas, abrir una cotización y la pestaña Documentos cargados. La galería incluye adjuntos binarios asociados al pedido y sus vínculos Studio compatibles. Cada tarjeta abre la vista previa; las imágenes se amplían al pulsarlas. Ver / actualizar documentos abre una consulta actualizada con modos galería y lista. Los documentos no se eliminan desde esta galería. Las miniaturas usan el lector existente de Odoo/Backblaze, sin duplicar imágenes en el filestore. Se respetan los permisos del usuario.
Actualizar el módulo incmd_b2_storage y recargar el navegador. Validación estática realizada; pendiente prueba funcional en Odoo.sh.

## Versión 28
La pestaña se incorpora al resolver el formulario, sin registrar una vista heredada de sale.order durante la actualización. Esto evita que la instalación de la galería active la validación del modificador personalizado validar_autorizaion. No modifica campos ni reglas comerciales de otras personalizaciones.

## Versión 29: corrección del parser Kanban
La pestaña Documentos cargados ahora contiene el botón Ver documentos cargados. Abre una ventana de galería/lista específica del pedido, con vistas independientes cargadas mediante el mecanismo normal de Odoo. No se inyectan subcampos de ir.attachment en los metadatos del formulario de sale.order. Cada apertura consulta los adjuntos actuales. Las tarjetas abren la vista previa, y la imagen permite abrir el original ampliado.

## Versión 30
En la vista previa de documentos guardados se oculta la barra binaria original (nombre duplicado, cambiar, descargar y eliminar). Se conserva el nombre dentro de la tarjeta y la vista previa ampliable. El selector nativo se muestra solo para documentos nuevos. Esta modificación es visual; no cambia las reglas de acceso del modelo.

## Versión 31
Visor carrusel compacto de 320 × 180 px dentro de Documentos cargados, sin botón de apertura de galería. Flechas anterior/siguiente, nombre y contador. Pulsar la imagen abre el original ampliado. Otros documentos muestran icono y enlace de apertura. Un icono de actualización consulta las últimas cargas sin salir del pedido. No descarga todos los originales para llenar el carrusel: obtiene metadatos y carga únicamente la miniatura visible. Se conservan los permisos de acceso y el almacenamiento existentes. Validación estática; pendiente prueba funcional en Odoo.sh.

## Versión 32: validación en Proyecto
En las tareas se agrega Documentos para validar con carrusel grande adaptable (hasta 1100 px de ancho, imagen de hasta 600 px de alto). Flechas, nombre, contador y apertura del original. Incluye adjuntos directos, de mensajes visibles del chatter, relaciones personalizadas a ir.attachment y documentos de la cotización vinculada por sale_order_id/sale_line_id cuando esos campos existen. Respeta permisos sin sudo; no copia archivos ni cambia su propietario. El carrusel de Ventas conserva su tamaño pequeño. El módulo no modifica el clip nativo del chatter; los documentos exclusivos de una cotización mantienen esa relación y no pasan a ser adjuntos directos de la tarea.

## Versión 33
Backblaze deja de ser una aplicación del menú principal. El menú existente se mueve bajo Ajustes (base.menu_administration), solo para administradores; se conservan sus identificadores y la configuración de repositorios, transferencias y monitoreo. No cambia el almacenamiento. El asunto del clip del chatter continúa pendiente de diagnóstico.

## Versión 34: clip del chatter de Proyecto
La respuesta de adjuntos del chatter nativo en project.task incluye los documentos visibles vinculados a la tarea y a su pedido, también mediante x_studio_pedido. Se conserva la lista nativa y se agregan IDs faltantes sin duplicados. No se cambia res_model/res_id, no se copian archivos ni se migran adjuntos. El carrusel usa la misma selección. Se mantiene la configuración bajo Ajustes. Esta corrección requiere validar el clip y la apertura de los documentos en Odoo.sh; no recupera relaciones de mensajes previamente eliminadas por otros módulos.


## v43 — limpieza sin bloqueo por referencias compartidas
Selecciona hasta 20 auditorías elegibles por ejecución usando SQL: excluye referencias locales de toda la tabla ir_attachment antes de aplicar el límite. Recomprueba referencias bajo el mismo bloqueo de tabla usado anteriormente. Las referencias locales se conservan y vuelven a ser elegibles automáticamente cuando desaparecen. Errores individuales quedan pendientes con detalle, contador y reintento en 30 minutos; los otros registros continúan. No modifica ni migra referencias de facturas automáticamente. El contador total incluye archivos compartidos que todavía no se pueden liberar.

Instalación: sustituir carpeta del módulo, desplegar y ACTUALIZAR el módulo para crear los tres campos nuevos. Cerrar y abrir consolas Odoo anteriores. El cron existente conserva su frecuencia por noupdate; la configuración actual de un minuto se mantiene. Probar primero en staging con un archivo sin referencias, otro compartido y uno con fallo de borrado. Revisar Historial y el log “B2 cleanup: selected=… confirmed=…”.


## v44 — históricos sin extensión

Opción «Permitir documentos sin extensión» por regla, activada inicialmente. Los adjuntos sin extensión deben cumplir el MIME, vínculo, tamaño y selección de repositorio. Los nombres con extensión conservan la lista permitida. JS, CSS, assets, HTML, fuentes, modelos técnicos y campos binarios no autorizados siguen excluidos. No se renombran documentos.

Actualizar el módulo desde Aplicaciones después de desplegar el código: la migración 17.0.1.0.44 habilita esta opción y reinicia los cursores una sola vez, conservando referencias remotas, auditorías y configuraciones de repositorio/cron. Corrige video/mp3 manual a audio/mpeg. El reinicio vuelve a examinar locales, no vuelve a subir los objetos b2v2://. Si solo se copia el código sin actualizar el módulo, la migración y el nuevo campo no se aplican.

Se conservan los límites configurados (en la instancia diagnosticada: 200/45 segundos), ventana horaria, contingencia, candados no bloqueantes, reintentos y limpieza v43 por referencia local real. Un lote puede durar más que el presupuesto por una llamada de red en curso. Al alcanzar max_attempts el archivo queda pendiente pero no vuelve a intentar automáticamente. La limpieza conserva archivos compartidos, pospone fallos y sigue con los demás. No se habilitan imágenes de producto automáticamente.

Validación en staging: comprobar la opción, cursor reiniciado, PDF 67045 elegible si las demás reglas no cambiaron, avance de auditorías/cursor y descarga del original remoto. La ejecución completa requiere Odoo y Backblaze; los controles locales no sustituyen esa prueba.

## Cambios 17.0.1.0.45
- Identificación conservadora de MIME y extensión faltantes antes de evaluar las reglas de migración; no cambia los bytes, `store_fname` ni `checksum`.
- Solo se normalizan archivos binarios de negocio asociados a modelos con reglas activas, nunca campos binarios del sistema, JS/CSS/assets o rutas remotas existentes.
- Detección mediante firmas binarias o estructuras ZIP de formatos conocidos; incompatibilidades o formatos desconocidos se dejan intactos.
- El cargador especial de cotizaciones intenta completar MIME faltante antes de la validación de formatos.
- Fallos individuales de transferencia dejan el adjunto pendiente con reintento y no detienen el resto del lote; se conserva límite temporal.
- El registro de error de limpieza se aísla con savepoint para que una auditoría fallida no impida procesar las demás.

**Antes de producción:** probar en staging con JPG/PNG/PDF y archivos ZIP de Office, validar reglas y descargas, y revisar `ir.logging`/logs. Las operaciones sobre archivos remotos existentes no renormalizan ni renombrarán referencias.

## v46: cola independiente de transferencias fallidas

- `batch_failure_limit = -1` significa que las fallas individuales no limitan el número de intentos del lote; aún se respetan tiempo y cantidad de candidatos. Valores positivos: 1 a 200.
- La tarea normal selecciona pendientes nunca fallidos (`b2_attempts=0`); los archivos fallidos (`b2_attempts>0`) quedan reservados a la tarea de reintentos diaria.
- La tarea de reintentos utiliza la hora local (`path_timezone`, `retry_hour`) y su propio cupo y presupuesto. Se crea o sincroniza con «Crear / actualizar tarea».
- La fecha `b2_next_try` y `max_attempts` se respetan también en los reintentos. `max_attempts=0` permite reintentos sin límite, pero se ejecutan solamente dentro del presupuesto y horario configurados.
- Si una transferencia se confirma, el adjunto pasa a `remote` y `b2_retry_queued=False`; sale automáticamente del listado de pendientes. La auditoría no se borra.
- `action_retry_batch` realiza una ejecución manual del lote de reintentos (si los intentos ya están vencidos). La limpieza sigue siendo independiente y exige verificación remota.
- Los archivos técnicos JS/CSS y assets permanecen excluidos por las reglas existentes; no se altera el contenido binario para normalizar MIME o extensión.

**Validación previa a producción:** probar creación de crons, carga, fallo simulado, reintento posterior, confirmación remota, descarga y limpieza con referencias compartidas en staging. Esta entrega fue validada sintácticamente, no ejecutada en un servidor Odoo real.
