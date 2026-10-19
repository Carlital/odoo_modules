
import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        const blocked_ctrl = this.config.disable_ctrl_p;
        const blocked_click = this.config.disable_right_click;
        if (!window._pos_shortcuts_blocked) {
            window._pos_shortcuts_blocked = true;

            if (blocked_ctrl) {
                window.addEventListener("keydown", (event) => {
                    if (event.ctrlKey && event.key === "p") {
                        event.preventDefault();
                        event.stopPropagation();
                        console.log("Ctrl+P deshabilitado");
                    }
                });
            }

            if (blocked_click) {
                window.addEventListener("contextmenu", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    console.log("Clic derecho deshabilitado");
                });
            }
        }
        
    },
});

