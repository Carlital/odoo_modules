
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";


export class AcsAlert {
    constructor(env, services) {
        /** @type {ReturnType<typeof import("@bus/services/bus_service").busService.start>} */
        this.busService = services.bus_service;
        this.dialog = services.dialog;
        
    }

    setup() {
        let uid = Array.isArray(session.user_id) ? session.user_id[0] : user.userId;
        if(uid){
            this.busService.addChannel('acs_alerts_'+uid);
            this.busService.subscribe('acs_alert', this._onGetAlert.bind(this));
        }
        
    }

    _onGetAlert(notification) {
        var self = this;
        // this.dialog.add(AlertDialog, {
        //     body: notification.message,
        // });
        const modal = document.createElement("div");
        modal.style.position = "fixed";
        modal.style.top = "0";
        modal.style.left = "0";
        modal.style.width = "100vw";
        modal.style.height = "100vh";
        modal.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
        modal.style.display = "flex";
        modal.style.justifyContent = "center";
        modal.style.alignItems = "center";
        modal.style.zIndex = "1000";

        // Contenedor del contenido del modal
        const modalContent = document.createElement("div");
        modalContent.style.backgroundColor = "white";
        modalContent.style.padding = "20px";
        modalContent.style.borderRadius = "10px";
        modalContent.style.boxShadow = "0 5px 15px rgba(0,0,0,0.3)";
        modalContent.style.width = "300px";
        modalContent.style.textAlign = "center";
        modalContent.innerHTML = notification.message;

        // Botón de cierre
        const closeButton = document.createElement("button");
        closeButton.innerText = "Cerrar";
        closeButton.style.marginTop = "10px";
        closeButton.style.padding = "8px 15px";
        closeButton.style.border = "none";
        closeButton.style.backgroundColor = "#ff5f5f";
        closeButton.style.color = "white";
        closeButton.style.borderRadius = "5px";
        closeButton.style.cursor = "pointer";

        // Evento para cerrar el modal
        closeButton.addEventListener("click", function () {
            modal.remove();
        });

        // Agregar elementos al modal
        modalContent.appendChild(closeButton);
        modal.appendChild(modalContent);

        // Agregar el modal al body
        document.getElementsByTagName("body")[0].appendChild(modal);
    }
}

export const acsAlert = {
    dependencies: ["bus_service","dialog"],
    start(env, services) {
        const history = new AcsAlert(env, services);
        history.setup();
    },
};

registry.category("services").add("acs_alerts.alertas", acsAlert);
