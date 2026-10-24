odoo.define('hide_pos_refund_button_knk.hide_refund_btn', [], function (require) {
    // Oculta el botón de reembolso
    function hideRefundButton() {
        try {
            let refundBtn = document.querySelector('.control-button i.fa-undo')?.closest('button');
            if (!refundBtn) {
                const buttons = document.querySelectorAll('.control-button');
                for (let btn of buttons) {
                    const text = btn.textContent || '';
                    if (text.includes('Reembolso') || text.includes('Refund')) {
                        refundBtn = btn;
                        break;
                    }
                }
            }
            if (refundBtn) {
                refundBtn.style.display = 'none';
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
    }

    // Oculta el botón "Guardar"
    function hideSaveButton() {
        try {
            // Buscar por data-control-button o por texto
            let saveBtn = document.querySelector('[data-control-button="point_of_sale.SaveButton"]');
            if (!saveBtn) {
                const buttons = document.querySelectorAll('.control-button');
                for (let btn of buttons) {
                    const text = btn.textContent || '';
                    if (text.includes('Guardar') || text.includes('Save')) {
                        saveBtn = btn;
                        break;
                    }
                }
            }
            if (saveBtn) {
                saveBtn.style.display = 'none';
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
    }

    function hideButtons() {
        hideRefundButton();
        hideSaveButton();
    }

    // MutationObserver para ambos botones
    function setupMutationObserver() {
        const observer = new MutationObserver(function(mutations) {
            hideButtons();
        });
        observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
    }

    // Polling para ambos botones
    let attempts = 0;
    const maxAttempts = 20;
    const checkInterval = setInterval(() => {
        if ((hideRefundButton() & hideSaveButton()) || ++attempts >= maxAttempts) {
            clearInterval(checkInterval);
        }
    }, 500);

    // MutationObserver cuando el DOM esté listo
    if (document.readyState === "loading") {
        document.addEventListener('DOMContentLoaded', setupMutationObserver);
    } else {
        setupMutationObserver();
    }

    // Ocultar botones en cada navegación del POS
    const originalPushState = history.pushState;
    history.pushState = function() {
        originalPushState.apply(this, arguments);
        setTimeout(hideButtons, 300);
    };
});