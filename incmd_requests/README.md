# Gestión de Solicitudes INCOMEL — Odoo 19 Community

Primera versión 19.0.1.0.0. Aplicación interna independiente, sin Enterprise ni Studio. Integra la aplicación Empleados (hr).

## Instalación

1. Descomprimir el ZIP. Copiar **incmd_requests** completo a una ruta incluida en `addons_path`. La carpeta debe contener directamente `__manifest__.py`; no anidar otra carpeta del mismo nombre.
2. Reiniciar Odoo para cargar el código Python.
3. En modo desarrollador: Aplicaciones → Actualizar lista de aplicaciones.
4. Buscar **Gestión de Solicitudes INCOMEL** e instalar. Aparecerá la aplicación **Solicitudes** con icono propio en el selector de aplicaciones. La presentación del selector depende del tema instalado en Community.

No usar «Importar módulo ZIP» para instalar: este addon contiene Python y debe estar en el servidor.

Con CLI, sobre una base de pruebas y adaptando las rutas:

```bash
./odoo-bin -c /etc/odoo/odoo.conf -d BASE_PRUEBAS -i incmd_requests --stop-after-init
```

Para actualizar código posteriormente: reiniciar y actualizar el módulo (`-u incmd_requests`).

## Primera configuración — orden recomendado

El usuario administrador principal de Odoo recibe el perfil Administrador del módulo al instalar.
Otros administradores se pueden asignar en Ajustes → Usuarios → Gestión de Solicitudes, o desde Configuración → Usuarios y perfiles.

1. **Áreas y tiendas:** crear las unidades y su compañía; indicar cuáles reciben solicitudes.
2. **Equipo de atención:** en cada área destinataria, elegir usuarios internos que atenderán el trabajo.
3. **Usuarios y perfiles:** asignar un área o tienda a cada usuario, por compañía. Elegir Usuario, Supervisor o Administrador. El perfil es global para el módulo; no concede administración general de Odoo.
4. **Supervisores:** en cada área o tienda, agregar los supervisores que la tienen a cargo. Un supervisor puede estar en varias unidades. Su propia unidad de origen puede ser distinta de las supervisadas.
5. **Procesos y versiones:** crear el proceso, guardar; agregar y guardar las etapas. Marcar exactamente una inicial y al menos un cierre. Definir quién atiende cada etapa.
6. **Acciones y rutas:** crear las acciones entre etapas ya guardadas. Ejemplo: Nueva → Diagnóstico; Diagnóstico → Reparación; Reparación → Resuelta. Cada etapa debe ser alcanzable y tener una ruta hasta un cierre. Agregar Rechazada como etapa de cierre si se necesita una acción de rechazo.
7. **Publicar versión.** La versión se vuelve inmutable.
8. **Motivos:** elegir el área y un proceso publicado de esa misma área. Varios motivos pueden compartir un proceso.

## Perfiles y visibilidad

- **Usuario:** crea sus solicitudes, edita sus borradores y consulta/responde las propias. Si pertenece al equipo destinatario o está autorizado en una etapa, también puede atender las solicitudes correspondientes.
- **Supervisor:** lo anterior, más lectura de las solicitudes enviadas **desde** las áreas/tiendas donde figura como supervisor. No ve borradores ajenos. La supervisión no concede automáticamente permiso para resolver; debe estar autorizado en la etapa.
- **Administrador:** configura el módulo y ve las solicitudes en sus compañías permitidas. Puede gestionar la atención, pero no editar el contenido original después del envío.

El menú Supervisión aplica un filtro por unidades de origen supervisadas. Las reglas de registros también restringen lectura por API, exportaciones y enlaces directos. Los perfiles autorizados por su participación pueden ver además los casos que atienden.

## Integración con Empleados

La ficha del empleado mantiene su vínculo al usuario de Odoo y su departamento. El módulo no convierte automáticamente a un jefe de departamento en Supervisor: la autorización debe asignarse expresamente.

Para usar la estructura existente:

1. En Áreas y tiendas, vincular cada área con el **Departamento de Empleados** correspondiente.
2. Verificar en Empleados que la ficha tenga usuario relacionado y compañía correctos.
3. Para tiendas o excepciones, completar **Área o tienda para solicitudes** en la ficha del empleado. Este campo lo puede ver un Administrador del módulo; para editar la ficha también necesita los permisos habituales de Empleados.
4. Asignar el perfil del módulo al usuario desde Ajustes → Usuarios, o desde Usuarios y perfiles.

Prioridad del origen: asignación directa usuario/unidad → unidad específica de la ficha del empleado → unidad vinculada a su departamento. La asignación directa es una excepción que prevalece; evite mantenerla si desea que los traslados en Empleados determinen automáticamente el origen. Si existen varias fichas del mismo usuario en la compañía, debe resolverse la ambigüedad o usar asignación directa.

No es obligatorio crear un empleado para cada usuario: puede utilizar asignación directa. El origen se conserva en las solicitudes enviadas aunque luego cambie la ficha del empleado.

## Tipos de responsable por etapa

- **Equipo destinatario:** miembros del equipo del área que recibe la solicitud.
- **Supervisor de origen:** usuarios con perfil Supervisor que figuran en la unidad de origen.
- **Usuarios específicos:** usuarios elegidos expresamente en la etapa.

El responsable individual de seguimiento debe pertenecer al equipo destinatario. Asignarlo no anula las autorizaciones de la etapa. El administrador puede ejecutar acciones como excepción operativa de atención; se registra su identidad.

## Uso diario

- Mis solicitudes → Nuevo → completar área destinataria, motivo, asunto, descripción y adjuntos → Enviar solicitud.
- El origen y solicitante son automáticos. Para crear se necesita una asignación válida en la compañía activa.
- Después de enviar: datos y adjuntos originales quedan bloqueados, incluso para el Administrador del módulo.
- **Registrar avance / Ejecutar acción:** escribir comentario, adjuntar evidencia y opcionalmente seleccionar una acción disponible. Sin acción, registra seguimiento sin mover la etapa.
- El solicitante usa **Responder / Aclarar**. También hay chatter nativo para conversación y actividades. Los cambios de etapa se realizan mediante el asistente para conservar la auditoría.
- **Tablero del proceso** abre Kanban filtrado a un proceso y versión. Sus columnas son sus propias etapas, incluidas las vacías. Las tarjetas no se arrastran: los cambios usan las acciones validadas.
- Las etapas de aprobación solo admiten Aprobar, Devolver o Rechazar; no se permite avance genérico. Si una etapa exige adjunto, se carga evidencia nueva en el asistente al ejecutar su acción.
- Todo seguimiento estructurado exige comentario. La evidencia y los mensajes enviados se conservan: para corregir, agregar otra aclaración.
- Las solicitudes cerradas no se reabren en esta versión. Los borradores solo los elimina su autor; las enviadas no se eliminan.

## Cambiar un flujo publicado

Abrir el proceso → Crear nueva versión → editar etapas y acciones → Publicar versión → cambiar el proceso de los motivos correspondientes. Las solicitudes enviadas mantienen el proceso anterior. Un borrador toma la versión configurada en el motivo en el momento de enviarse.

## Diseño y alcance

Vistas nativas Odoo: listas, formularios, Kanban, chatter, tablas dinámicas y gráficos; icono propio y estilos discretos. Los mockups son referencias de diseño, no una reproducción exacta de cada píxel ni un cambio completo del tema Community. Las pantallas respetan el tema existente.

Incluye separación por compañías, historial, aprobaciones y rutas de devolución/rechazo. No incluye portal, campos dinámicos por motivo, SLA/calendarios laborales, firma digital, automatizaciones de correo externas ni rutas condicionales por monto. «Firma» es una etapa de aprobación, no una firma electrónica.

## Validación y pruebas

Se validaron sintaxis Python, manifiesto, referencias XML/CSV y arquitecturas de listas, búsqueda y pivote con los validadores oficiales descargados de Odoo 19. Se incluyen pruebas `TransactionCase` para aislamiento de supervisores, borradores, perfiles, inmutabilidad, adjuntos, seguimiento y versiones.

**Pendiente:** ejecutar las pruebas de integración e instalar en una instancia real de Odoo 19 Community. Este entorno no dispone de un PostgreSQL ejecutable con el usuario requerido; no se presenta la validación estática como una instalación exitosa.

Ejecutar sobre una base desechable, con el módulo instalado:

```bash
./odoo-bin -c /etc/odoo/odoo.conf -d BASE_PRUEBAS -u incmd_requests --test-enable --test-tags /incmd_requests --stop-after-init
```

Probar primero con tres usuarios y dos tiendas antes de producción. Configurar equipos y supervisores antes de enviar solicitudes para que las autorizaciones sean efectivas.
