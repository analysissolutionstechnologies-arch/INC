/** Filtros en cascada para categoría, motivo y submotivo */
odoo.define('incmd_tickets.ticket_form_customization', [], function (require) {
    'use strict';
    
    const inicializar = function() {
        const categoriaSelect = document.querySelector('select[name="x_studio_categoria"]');
        const motivoSelect = document.querySelector('select[name="x_studio_motivo"]');
        const submotivoSelect = document.querySelector('select[name="x_studio_submotivo"]');
        if (!categoriaSelect || !motivoSelect || !submotivoSelect) return;

        function deshabilitarCamposSecundarios() {
            motivoSelect.disabled = true;
            motivoSelect.innerHTML = '<option value="">Seleccione una categoría primero</option>';
            submotivoSelect.disabled = true;
            submotivoSelect.innerHTML = '<option value="">Seleccione un motivo primero</option>';
        }

        function cargarCategorias() {
            fetch('/tickets/filtrar_motivos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    id: Math.floor(Math.random() * 1000000),
                    params: { parent_id: null, equipo_id: 1 }
                }),
            })
            .then(response => response.json())
            .then(data => {
                const categorias = Array.isArray(data.result) ? data.result : [];
                categoriaSelect.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Seleccione categoría...';
                categoriaSelect.appendChild(defaultOption);
                if (categorias.length > 0) {
                    categorias.forEach(categoria => {
                        const option = document.createElement('option');
                        option.value = categoria.id;
                        option.textContent = categoria.x_name;
                        categoriaSelect.appendChild(option);
                    });
                }
                if (!categoriaSelect.value) deshabilitarCamposSecundarios();
            })
            .catch(() => { deshabilitarCamposSecundarios(); });
        }

        function cargarMotivos(categoriaId) {
            if (!categoriaId) {
                deshabilitarCamposSecundarios();
                return;
            }
            motivoSelect.disabled = true;
            motivoSelect.innerHTML = '<option value="">Cargando motivos...</option>';
            submotivoSelect.innerHTML = '<option value="">Seleccione un motivo primero</option>';
            submotivoSelect.disabled = true;
            fetch('/tickets/filtrar_motivos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    id: Math.floor(Math.random() * 1000000),
                    params: { parent_id: categoriaId, equipo_id: 1 }
                }),
            })
            .then(response => response.json())
            .then(data => {
                const motivos = Array.isArray(data.result) ? data.result : [];
                motivoSelect.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Seleccione motivo...';
                motivoSelect.appendChild(defaultOption);
                if (motivos.length === 0) {
                    const emptyOption = document.createElement('option');
                    emptyOption.value = '';
                    emptyOption.textContent = 'No hay motivos disponibles';
                    motivoSelect.appendChild(emptyOption);
                } else {
                    motivos.forEach(motivo => {
                        const option = document.createElement('option');
                        option.value = motivo.id;
                        option.textContent = motivo.x_name;
                        motivoSelect.appendChild(option);
                    });
                }
                motivoSelect.disabled = motivos.length === 0;
            })
            .catch(() => {
                motivoSelect.innerHTML = '<option value="">Error al cargar</option>';
                motivoSelect.disabled = true;
            });
        }

        function cargarSubmotivos(motivoId) {
            if (!motivoId) {
                submotivoSelect.innerHTML = '<option value="">Seleccione un motivo primero</option>';
                submotivoSelect.disabled = true;
                return;
            }
            submotivoSelect.disabled = true;
            submotivoSelect.innerHTML = '<option value="">Cargando submotivos...</option>';
            fetch('/tickets/filtrar_motivos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    id: Math.floor(Math.random() * 1000000),
                    params: { parent_id: motivoId, equipo_id: 1 }
                }),
            })
            .then(response => response.json())
            .then(data => {
                const submotivos = Array.isArray(data.result) ? data.result : [];
                submotivoSelect.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Seleccione submotivo...';
                submotivoSelect.appendChild(defaultOption);
                if (submotivos.length === 0) {
                    const emptyOption = document.createElement('option');
                    emptyOption.value = '';
                    emptyOption.textContent = 'No hay submotivos disponibles';
                    submotivoSelect.appendChild(emptyOption);
                } else {
                    submotivos.forEach(submotivo => {
                        const option = document.createElement('option');
                        option.value = submotivo.id;
                        option.textContent = submotivo.x_name;
                        submotivoSelect.appendChild(option);
                    });
                }
                submotivoSelect.disabled = submotivos.length === 0;
            })
            .catch(() => {
                submotivoSelect.innerHTML = '<option value="">Error al cargar submotivos</option>';
                submotivoSelect.disabled = true;
            });
        }

        categoriaSelect.addEventListener('change', function() {
            const categoriaId = this.value;
            cargarMotivos(categoriaId);
        });
        motivoSelect.addEventListener('change', function() {
            const motivoId = this.value;
            cargarSubmotivos(motivoId);
        });

        deshabilitarCamposSecundarios();
        cargarCategorias();
        setTimeout(() => {
            const categoriaInicial = categoriaSelect.value;
            if (categoriaInicial) {
                cargarMotivos(categoriaInicial);
                setTimeout(() => {
                    const motivoInicial = motivoSelect.value;
                    if (motivoInicial) {
                        cargarSubmotivos(motivoInicial);
                    }
                }, 500);
            } else {
                deshabilitarCamposSecundarios();
            }
        }, 500);
    };
    
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(inicializar, 1500);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(inicializar, 1500);
        });
    }
    return {};
});