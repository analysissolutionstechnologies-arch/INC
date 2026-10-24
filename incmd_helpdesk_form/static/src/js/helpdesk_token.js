/* static/src/js/helpdesk_token.js */

(function() {
    'use strict';

    function iniciarScript() {
        var vendedorTransformado = false;
        var modalIniciada = false;
        var productosIniciados = false;
        var asuntoOculto = false;
        var agenciaSeleccionadaNombre = "";
        var tokenValidadoGuardado = "";

        function abrir(id) {
            var el = document.getElementById(id);
            if (el) {
                el.style.display = 'block';
                el.classList.add('show');
                el.style.zIndex = '1055';
            }
        }

        function cerrar(id) {
            var el = document.getElementById(id);
            if (el) {
                el.style.display = 'none';
                el.classList.remove('show');
            }
        }

        function setCorreoAlerta(valor) {
            var inputCorreoAlerta = document.getElementById('x_studio_correo_alerta');
            if (inputCorreoAlerta) {
                inputCorreoAlerta.value = valor || "";
                inputCorreoAlerta.dispatchEvent(new Event('input', { bubbles: true }));
                inputCorreoAlerta.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }

        function moverBloqueSolicitudDebajoVendedor() {
            var selectVendedor = document.querySelector('select[name="x_studio_vendedor"]');
            var bloque = document.getElementById('bloque_solicitud_creacion_vendedor');

            if (!selectVendedor || !bloque) {
                return;
            }

            if (bloque.dataset.movidoDebajoVendedor === "1") {
                return;
            }

            var contenedorCampo = selectVendedor.closest('.s_website_form_field') || selectVendedor.parentElement;
            if (!contenedorCampo || !contenedorCampo.parentNode) {
                return;
            }

            contenedorCampo.parentNode.insertBefore(bloque, contenedorCampo.nextSibling);
            bloque.dataset.movidoDebajoVendedor = "1";
        }

        function toggleCamposSolicitudCreacion() {
            var selectVendedor = document.querySelector('select[name="x_studio_vendedor"]');
            var contenedor = document.getElementById('bloque_solicitud_creacion_vendedor');
            var inputNombre = document.querySelector('input[name="x_studio_nombre_vendedor_nuevo"]');
            var inputDpi = document.querySelector('input[name="x_studio_dpi_vendedor_nuevo"]');

            if (!selectVendedor || !contenedor) {
                return;
            }

            if (selectVendedor.value === "__solicitud_creacion__") {
                contenedor.style.display = '';
                if (inputNombre) {
                    inputNombre.required = true;
                }
                if (inputDpi) {
                    inputDpi.required = true;
                }
            } else {
                contenedor.style.display = 'none';
                if (inputNombre) {
                    inputNombre.required = false;
                    inputNombre.value = '';
                }
                if (inputDpi) {
                    inputDpi.required = false;
                    inputDpi.value = '';
                }
            }
        }

        function actualizarDatosAutomaticos() {
            var inputAsunto = document.querySelector('input[name="name"]');
            var inputDescripcion = document.getElementById('hidden_description_field');
            var inputTienda = document.querySelector('input[name="x_studio_contabilidad_singergias_bda"]');
            var selectVendedor = document.querySelector('select[name="x_studio_vendedor"]');
            var inputNombreNuevo = document.querySelector('input[name="x_studio_nombre_vendedor_nuevo"]');
            var inputDpiNuevo = document.querySelector('input[name="x_studio_dpi_vendedor_nuevo"]');

            if (inputTienda && selectVendedor) {
                var textoTienda = inputTienda.value || "";
                var textoVendedor = selectVendedor.value || "";

                if (inputAsunto) {
                    var asunto = "";

                    if (textoTienda !== "") {
                        asunto += textoTienda;
                    }

                    if (tokenValidadoGuardado !== "") {
                        asunto += " - " + tokenValidadoGuardado;
                    }

                    inputAsunto.value = asunto;
                    inputAsunto.dispatchEvent(new Event('input', { bubbles: true }));
                    inputAsunto.dispatchEvent(new Event('change', { bubbles: true }));
                }

                if (inputDescripcion) {
                    var reporte = "";
                    var filasProductos = document.querySelectorAll('#ui_tabla_productos_visual tbody tr');

                    if (filasProductos.length > 0) {
                        reporte += "DETALLE DE PRODUCTOS\n";
                        reporte += "==================================================\n\n";

                        filasProductos.forEach(function(row) {
                            if (!row.cells || row.cells.length < 2) {
                                return;
                            }

                            var celdaNombre = row.cells[0].innerText.replace(/\n/g, " ");
                            var inputCant = row.cells[1].querySelector('input');
                            var valorCant = "0";

                            if (inputCant) {
                                var num = parseInt(inputCant.value, 10);
                                if (isNaN(num) || num < 1) {
                                    inputCant.value = 1;
                                    valorCant = "1";
                                } else {
                                    valorCant = inputCant.value;
                                }
                            }

                            reporte += "+ CANTIDAD: [ " + valorCant + " ]\n";
                            reporte += "  PRODUCTO: " + celdaNombre + "\n";
                            reporte += "__________________________________________________\n\n";
                        });
                    }

                    inputDescripcion.value = reporte;
                    inputDescripcion.dispatchEvent(new Event('input', { bubbles: true }));
                    inputDescripcion.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        }

        function filtrarVendedoresPorAgencia(nombreAgencia) {
            var selectVendedor = document.querySelector('select[name="x_studio_vendedor"]');
            if (!selectVendedor) {
                return;
            }

            selectVendedor.innerHTML = "";

            var optDef = document.createElement('option');
            optDef.value = "";
            optDef.text = "Seleccione un vendedor...";
            selectVendedor.appendChild(optDef);

            if (window.mis_empleados_odoo) {
                var empleadosFiltrados = window.mis_empleados_odoo.filter(function(e) {
                    return e.dept === nombreAgencia;
                });

                empleadosFiltrados.forEach(function(emp) {
                    var opt = document.createElement('option');
                    opt.value = emp.name;
                    opt.text = emp.name;
                    selectVendedor.appendChild(opt);
                });
            }

            var optSolicitud = document.createElement('option');
            optSolicitud.value = "__solicitud_creacion__";
            optSolicitud.text = "No existe / Solicitud creación";
            selectVendedor.appendChild(optSolicitud);

            toggleCamposSolicitudCreacion();
        }

        function iniciarLogicaProductos() {
            if (productosIniciados) {
                return;
            }

            var inputBuscar = document.getElementById('ui_buscar_producto');
            var dataList = document.getElementById('lista_sugerencias_productos');
            var btnAgregar = document.getElementById('btn_agregar_producto');
            var msgVacio = document.getElementById('msg_sin_productos');

            if (inputBuscar && dataList && btnAgregar && window.mis_productos_odoo) {
                window.mis_productos_odoo
                    .filter(function(p) {
                        return p.qty_available > 0;
                    })
                    .forEach(function(p) {
                        var opt = document.createElement('option');
                        var valor = p.name;
                        if (p.barcode) {
                            valor = "[" + p.barcode + "] " + valor;
                        }
                        opt.value = valor;
                        dataList.appendChild(opt);
                    });

                btnAgregar.addEventListener('click', function(e) {
                    e.preventDefault();

                    var val = inputBuscar.value;
                    if (!val) {
                        return;
                    }

                    msgVacio.style.display = 'none';

                    var tr = document.createElement('tr');

                    var productoEncontrado = window.mis_productos_odoo.find(function(p) {
                        var nombreCompleto = p.name;
                        if (p.barcode) {
                            nombreCompleto = "[" + p.barcode + "] " + p.name;
                        }
                        return nombreCompleto === val;
                    });

                    var contenidoNombre = val;
                    if (productoEncontrado && productoEncontrado.mis_atributos && productoEncontrado.mis_atributos !== "") {
                        contenidoNombre += "<br><span style='font-size:0.85em; color:#666; font-style:italic;'>" + productoEncontrado.mis_atributos + "</span>";
                    }

                    var tdName = document.createElement('td');
                    tdName.className = "ps-3 fw-bold text-dark";
                    tdName.innerHTML = contenidoNombre;
                    tr.appendChild(tdName);

                    var tdQty = document.createElement('td');
                    var inpQty = document.createElement('input');
                    inpQty.type = 'number';
                    inpQty.className = 'form-control form-control-sm text-center';
                    inpQty.value = 1;
                    inpQty.min = 1;
                    inpQty.addEventListener('change', actualizarDatosAutomaticos);
                    tdQty.appendChild(inpQty);
                    tr.appendChild(tdQty);

                    var tdDel = document.createElement('td');
                    var btnDel = document.createElement('button');
                    btnDel.className = 'btn btn-sm btn-outline-danger border-0';
                    btnDel.textContent = 'X';
                    btnDel.onclick = function() {
                        tr.remove();

                        var quedanFilas = document.querySelectorAll('#ui_tabla_productos_visual tbody tr').length;
                        if (quedanFilas === 0 && msgVacio) {
                            msgVacio.style.display = 'block';
                        }

                        actualizarDatosAutomaticos();
                    };
                    tdDel.appendChild(btnDel);
                    tr.appendChild(tdDel);

                    document.querySelector('#ui_tabla_productos_visual tbody').appendChild(tr);
                    inputBuscar.value = "";
                    actualizarDatosAutomaticos();
                });

                productosIniciados = true;
            }
        }

        function iniciarModal() {
            if (modalIniciada) {
                return;
            }

            var inputTienda = document.querySelector('input[name="x_studio_contabilidad_singergias_bda"]');
            var selectModal = document.getElementById('ui_select_agencia_modal');
            var areaToken = document.getElementById('area_validacion_token');
            var btnEnviarToken = document.getElementById('btn_enviar_token');
            var msgTokenEnviado = document.getElementById('msg_token_enviado');
            var msgTokenError = document.getElementById('msg_token_error');
            var btnConfirmar = document.getElementById('btn_confirmar_agencia');

            var btnVerificar = document.getElementById('btn_verificar_token_final');
            var inputTokenUser = document.getElementById('input_token_usuario');
            var msgErrorToken = document.getElementById('msg_error_token');

            if (inputTienda && selectModal && window.mis_departamentos_odoo) {
                var contenedor = inputTienda.closest('.s_website_form_field');
                if (contenedor) {
                    contenedor.style.display = 'none';
                } else {
                    inputTienda.style.display = 'none';
                }

                if (selectModal.options.length <= 1) {
                    window.mis_departamentos_odoo.forEach(function(dep) {
                        var opt = document.createElement('option');
                        opt.value = dep.name;
                        opt.text = dep.name;
                        opt.setAttribute('data-email', dep.email || "");
                        selectModal.appendChild(opt);
                    });
                }

                abrir('modalSeleccion');

                selectModal.addEventListener('change', function() {
                    var selectedOption = selectModal.options[selectModal.selectedIndex];
                    var email = selectedOption.getAttribute('data-email');
                    agenciaSeleccionadaNombre = selectModal.value;

                    setCorreoAlerta(email);

                    msgTokenEnviado.classList.add('d-none');
                    msgTokenError.classList.add('d-none');

                    if (email && email.trim() !== "") {
                        areaToken.classList.remove('d-none');
                        btnConfirmar.disabled = true;
                    } else {
                        areaToken.classList.add('d-none');
                        btnConfirmar.disabled = false;
                    }
                });

                if (btnEnviarToken) {
                    var newBtnToken = btnEnviarToken.cloneNode(true);
                    btnEnviarToken.parentNode.replaceChild(newBtnToken, btnEnviarToken);

                    newBtnToken.addEventListener('click', function() {
                        var selectedOption = selectModal.options[selectModal.selectedIndex];
                        var emailDestino = selectedOption.getAttribute('data-email');

                        setCorreoAlerta(emailDestino);

                        newBtnToken.disabled = true;
                        newBtnToken.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Enviando...';

                        var payload = {
                            jsonrpc: "2.0",
                            method: "call",
                            id: Math.floor(Math.random() * 1000000),
                            params: {
                                email: emailDestino,
                                agencia: agenciaSeleccionadaNombre
                            }
                        };

                        fetch("/helpdesk/enviar_token", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify(payload)
                        })
                        .then(function(res) {
                            return res.json();
                        })
                        .then(function(data) {
                            if (data.result && data.result.success) {
                                newBtnToken.innerHTML = '<i class="fa fa-check"></i> Enviado';
                                msgTokenEnviado.classList.remove('d-none');
                                cerrar('modalSeleccion');
                                abrir('modalIngresoToken');
                            } else {
                                newBtnToken.disabled = false;
                                newBtnToken.innerHTML = 'Reintentar';
                                msgTokenError.classList.remove('d-none');
                            }
                        })
                        .catch(function() {
                            newBtnToken.disabled = false;
                            newBtnToken.innerHTML = 'Error Red';
                            msgTokenError.classList.remove('d-none');
                        });
                    });
                }

                if (btnVerificar) {
                    var newBtnVerificar = btnVerificar.cloneNode(true);
                    btnVerificar.parentNode.replaceChild(newBtnVerificar, btnVerificar);

                    newBtnVerificar.addEventListener('click', function() {
                        var codigoIngresado = (inputTokenUser.value || "").trim();
                        if (!codigoIngresado) {
                            return;
                        }

                        newBtnVerificar.disabled = true;
                        newBtnVerificar.textContent = "Verificando...";
                        msgErrorToken.classList.add('d-none');

                        var payloadVal = {
                            jsonrpc: "2.0",
                            method: "call",
                            id: Math.floor(Math.random() * 1000000),
                            params: {
                                token: codigoIngresado,
                                agencia: agenciaSeleccionadaNombre
                            }
                        };

                        fetch("/helpdesk/validar_token", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify(payloadVal)
                        })
                        .then(function(res) {
                            return res.json();
                        })
                        .then(function(data) {
                            if (data.result && data.result.success) {
                                tokenValidadoGuardado = codigoIngresado;

                                cerrar('modalIngresoToken');
                                inputTienda.value = agenciaSeleccionadaNombre;
                                inputTienda.dispatchEvent(new Event('input', { bubbles: true }));
                                inputTienda.dispatchEvent(new Event('change', { bubbles: true }));

                                var etiqueta = document.getElementById('visual_tienda_name');
                                if (etiqueta) {
                                    etiqueta.textContent = agenciaSeleccionadaNombre;
                                }

                                setCorreoAlerta(selectModal.options[selectModal.selectedIndex].getAttribute('data-email'));

                                filtrarVendedoresPorAgencia(agenciaSeleccionadaNombre);
                                actualizarDatosAutomaticos();
                                abrir('modalExito');

                                setTimeout(function() {
                                    cerrar('modalExito');
                                }, 1500);
                            } else {
                                msgErrorToken.textContent = "CÓDIGO INCORRECTO O VENCIDO";
                                msgErrorToken.classList.remove('d-none');
                                newBtnVerificar.disabled = false;
                                newBtnVerificar.textContent = "VERIFICAR";
                            }
                        })
                        .catch(function() {
                            msgErrorToken.textContent = "ERROR AL VALIDAR EL CÓDIGO";
                            msgErrorToken.classList.remove('d-none');
                            newBtnVerificar.disabled = false;
                            newBtnVerificar.textContent = "VERIFICAR";
                        });
                    });
                }

                var btn = document.getElementById('btn_confirmar_agencia');
                if (btn) {
                    var newBtn = btn.cloneNode(true);
                    btn.parentNode.replaceChild(newBtn, btn);

                    newBtn.addEventListener('click', function(e) {
                        e.preventDefault();

                        var val = selectModal.value;
                        if (val && val !== "") {
                            tokenValidadoGuardado = "";
                            inputTienda.value = val;
                            inputTienda.dispatchEvent(new Event('input', { bubbles: true }));
                            inputTienda.dispatchEvent(new Event('change', { bubbles: true }));

                            var visual = document.getElementById('visual_tienda_name');
                            if (visual) {
                                visual.textContent = val;
                            }

                            setCorreoAlerta(selectModal.options[selectModal.selectedIndex].getAttribute('data-email'));

                            filtrarVendedoresPorAgencia(val);
                            actualizarDatosAutomaticos();
                            abrir('modalExito');
                            cerrar('modalSeleccion');

                            setTimeout(function() {
                                cerrar('modalExito');
                            }, 1500);
                        }
                    });
                }

                modalIniciada = true;
            }
        }

        function transformarVendedor() {
            if (vendedorTransformado) {
                return;
            }

            var inputOriginal = document.querySelector('input[name="x_studio_vendedor"]');
            if (inputOriginal) {
                var nuevoSelect = document.createElement('select');
                nuevoSelect.className = inputOriginal.className + " form-select";
                nuevoSelect.name = "x_studio_vendedor";
                nuevoSelect.style.marginBottom = "0px";

                var optDefault = document.createElement('option');
                optDefault.value = "";
                optDefault.text = "Seleccione primero la agencia...";
                nuevoSelect.appendChild(optDefault);

                inputOriginal.removeAttribute('name');
                inputOriginal.removeAttribute('required');

                if (inputOriginal.parentNode) {
                    inputOriginal.parentNode.replaceChild(nuevoSelect, inputOriginal);
                }

                nuevoSelect.addEventListener('change', function() {
                    toggleCamposSolicitudCreacion();
                    actualizarDatosAutomaticos();
                });

                vendedorTransformado = true;
            }
        }

        function ocultarAsunto() {
            var inputAsunto = document.querySelector('input[name="name"]');
            if (inputAsunto) {
                var contenedor = inputAsunto.closest('.s_website_form_field');
                if (contenedor) {
                    contenedor.style.display = 'none';
                    asuntoOculto = true;
                }
            }
        }

        function iniciarEventosSolicitudCreacion() {
            var inputNombre = document.querySelector('input[name="x_studio_nombre_vendedor_nuevo"]');
            var inputDpi = document.querySelector('input[name="x_studio_dpi_vendedor_nuevo"]');

            if (inputNombre && !inputNombre.dataset.eventoCreacion) {
                inputNombre.dataset.eventoCreacion = "1";
                inputNombre.addEventListener('input', actualizarDatosAutomaticos);
            }

            if (inputDpi && !inputDpi.dataset.eventoCreacion) {
                inputDpi.dataset.eventoCreacion = "1";
                inputDpi.addEventListener('input', function() {
                    this.value = (this.value || '').replace(/\D/g, '').slice(0, 13);
                    actualizarDatosAutomaticos();
                });
            }
        }

        function completarCamposRequeridosPublico() {
            var inputAsunto = document.querySelector('input[name="name"]');
            var inputPartnerName = document.querySelector('input[name="partner_name"]');
            var inputPartnerEmail = document.querySelector('input[name="partner_email"]');
            var inputTienda = document.querySelector('input[name="x_studio_contabilidad_singergias_bda"]');
            var inputTelefono = document.querySelector('input[name="Número para contacto"]');
            var inputNombreSolicitante = document.querySelector('input[name="Nombre solicitante"]');
            var inputCategoria = document.querySelector('select[name="x_studio_categoria"], input[name="x_studio_categoria"]');
            var inputIP = document.querySelector('input[name="Numero de IP"]');
            var inputDescripcion = document.getElementById('hidden_description_field');
            var inputCorreoAlerta = document.getElementById('x_studio_correo_alerta');

            if (inputCorreoAlerta && (!inputCorreoAlerta.value || inputCorreoAlerta.value.trim() === "")) {
                var selectModal = document.getElementById('ui_select_agencia_modal');
                if (selectModal && selectModal.selectedIndex >= 0) {
                    var selectedOption = selectModal.options[selectModal.selectedIndex];
                    if (selectedOption) {
                        inputCorreoAlerta.value = selectedOption.getAttribute('data-email') || "";
                    }
                }
            }

            if (inputNombreSolicitante && (!inputNombreSolicitante.value || inputNombreSolicitante.value.trim() === "")) {
                inputNombreSolicitante.value = "AGENCIAS BDA";
            }

            if (inputPartnerName && (!inputPartnerName.value || inputPartnerName.value.trim() === "")) {
                if (inputNombreSolicitante && inputNombreSolicitante.value.trim() !== "") {
                    inputPartnerName.value = inputNombreSolicitante.value.trim();
                } else {
                    inputPartnerName.value = "AGENCIAS BDA";
                }
            }

            if (inputPartnerEmail && (!inputPartnerEmail.value || inputPartnerEmail.value.trim() === "")) {
                inputPartnerEmail.value = "TICKET_AGENCIAS_BDA@INCOMEL.COM.GT";
            }

            if (inputTienda && (!inputTienda.value || inputTienda.value.trim() === "")) {
                var visualTienda = document.getElementById('visual_tienda_name');
                if (visualTienda && visualTienda.textContent.trim() !== "" && visualTienda.textContent.trim() !== "Esperando selección...") {
                    inputTienda.value = visualTienda.textContent.trim();
                } else {
                    inputTienda.value = "SINERGIA";
                }
            }

            if (inputTelefono && (!inputTelefono.value || inputTelefono.value.trim() === "")) {
                inputTelefono.value = "00000000";
            }

            if (inputIP && (!inputIP.value || inputIP.value.trim() === "")) {
                inputIP.value = "0.0.0.0";
            }

            if (inputCategoria && (!inputCategoria.value || inputCategoria.value.trim() === "")) {
                if (inputCategoria.tagName === "SELECT") {
                    var opcionValida = Array.prototype.slice.call(inputCategoria.options).find(function(opt) {
                        return opt.value && opt.value.trim() !== "";
                    });
                    if (opcionValida) {
                        inputCategoria.value = opcionValida.value;
                    }
                } else {
                    inputCategoria.value = "FACTURACION SINERGIA";
                }
            }

            if (inputAsunto && (!inputAsunto.value || inputAsunto.value.trim() === "")) {
                var tiendaTexto = inputTienda && inputTienda.value ? inputTienda.value.trim() : "SINERGIA";
                inputAsunto.value = "Solicitud Facturación - " + tiendaTexto;
            }

            if (inputDescripcion && (!inputDescripcion.value || inputDescripcion.value.trim() === "")) {
                inputDescripcion.value = "Solicitud generada desde formulario web de Facturación Sinergia.";
            }

            [
                inputAsunto,
                inputPartnerName,
                inputPartnerEmail,
                inputTienda,
                inputTelefono,
                inputNombreSolicitante,
                inputCategoria,
                inputIP,
                inputDescripcion,
                inputCorreoAlerta
            ].forEach(function(campo) {
                if (campo) {
                    campo.dispatchEvent(new Event('input', { bubbles: true }));
                    campo.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }

        function asegurarDefaultsAntesDeEnviar() {
            var form = document.querySelector('form');
            if (!form) {
                return;
            }
            if (form.dataset.defaultsPublicoIniciado === "1") {
                return;
            }

            form.dataset.defaultsPublicoIniciado = "1";

            form.addEventListener('submit', function() {
                completarCamposRequeridosPublico();
                actualizarDatosAutomaticos();
            });
        }

        var intentos = 0;
        var intervalo = setInterval(function() {
            intentos++;

            if (!asuntoOculto) {
                ocultarAsunto();
            }
            if (!vendedorTransformado) {
                transformarVendedor();
            }
            if (!modalIniciada) {
                iniciarModal();
            }
            if (!productosIniciados) {
                iniciarLogicaProductos();
            }

            moverBloqueSolicitudDebajoVendedor();
            iniciarEventosSolicitudCreacion();
            completarCamposRequeridosPublico();
            asegurarDefaultsAntesDeEnviar();

            if (vendedorTransformado && modalIniciada && asuntoOculto && productosIniciados) {
                clearInterval(intervalo);
            }
            if (intentos > 50) {
                clearInterval(intervalo);
            }
        }, 200);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciarScript);
    } else {
        iniciarScript();
    }

})();