/** @odoo-module **/

import { AttachmentUploadService } from "@mail/core/common/attachment_upload_service";
import { patch } from "@web/core/utils/patch";

patch(AttachmentUploadService.prototype, {
    setup(env, services) {
        super.setup(env, services);
        // Odoo 17 no limpia correctamente el estado de subida del chatter
        // cuando una subida falla (status != 200 o respuesta con
        // {error: ...}). El handler original de FILE_UPLOAD_LOADED hace
        // return sin:
        //   1. Eliminar el attachment temporal del store (spinner del card
        //      colgado indefinidamente).
        //   2. Resolver el Deferred retornado por uploadFile (el flag
        //      isUploading de FileUploader nunca vuelve a false, dejando
        //      el texto "Uploading..." visible permanentemente).
        //
        // Este listener se ejecuta despues del handler original (FIFO) y
        // completa la limpieza en ambos casos. Al ser Composer.attachments
        // una relacion Record.many("Attachment"), el store elimina
        // automaticamente la referencia del composer al borrar el attachment.
        this.fileUploadService.bus.addEventListener(
            "FILE_UPLOAD_LOADED",
            ({ detail: { upload } }) => {
                const tmpId = parseInt(upload.data.get("temporary_id"));
                let hasError = false;
                if (upload.xhr.status !== 200) {
                    hasError = true;
                } else {
                    try {
                        const response = JSON.parse(upload.xhr.response);
                        if (response.error) {
                            hasError = true;
                        }
                    } catch (e) {
                        hasError = true;
                    }
                }
                if (hasError) {
                    const tmpAttachment = this.store.Attachment.get(tmpId);
                    if (tmpAttachment) {
                        this.attachmentService.remove(tmpAttachment);
                    }
                    const def = this.deferredByAttachmentId.get(tmpId);
                    if (def) {
                        def.resolve();
                        this.deferredByAttachmentId.delete(tmpId);
                    }
                }
            }
        );
    },
});
