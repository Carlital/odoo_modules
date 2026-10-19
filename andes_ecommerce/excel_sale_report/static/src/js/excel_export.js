/** @odoo-module **/

import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");

actionRegistry.add("export_excel_action", {
    async execute(action) {
        const { url } = action;
        if (!url) {
            console.error("No se proporcionó una URL para la exportación.");
            return;
        }
        this.env.services.ui.block();
        try {
            window.open(url, "_self");
        } catch (error) {
            console.error("Error durante la exportación:", error);
        } finally {
            this.env.services.ui.unblock();
        }
    },
});
