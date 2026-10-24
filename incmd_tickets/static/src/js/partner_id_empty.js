odoo.define('incmd_tickets.partner_id_empty', [], function (require) {
    'use strict';

    function agregarPartnerIdVacio() {
        console.log('[partner_id_empty] Ejecutando agregarPartnerIdVacio');
        document.querySelectorAll('form.o_mark_required').forEach(function(form) {
            if (!form.querySelector('input[name="partner_id"]')) {
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'partner_id';
                input.value = '';
                form.appendChild(input);
                console.log('[partner_id_empty] Campo partner_id vacío agregado al formulario:', form);
            } else {
                console.log('[partner_id_empty] El formulario ya tiene partner_id:', form);
            }
        });
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(agregarPartnerIdVacio, 500);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(agregarPartnerIdVacio, 500);
        });
    }
});