/** @odoo-module **/

import { loadBundle, loadJS } from "@web/core/assets";
import { Component, onMounted, onWillUnmount, useRef, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";

class NoticesTemplate extends Component {
    static template = "odoo-mercadolibre.notices";

    async setup() {
        this.rpc = useService("rpc");  // Using the RPC service
        this.action = useService("action");  // Using the Action service to open the view

        self = this.action; // Ensure self is set in the constructor

        this.http = useService("http");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");
        this.state = useState({
            title: "",
            description: "",
            dataPublications: [],
            //dataPublications: [],
            filterByDate: "last_7",
            startDate: "",
            endDate: "",
            showDateFilter: false,
        });

        onWillStart(async () => {
            this.test();
        });

        //onWillUnmount(() => { this.onWillUnmount() });
    }

    async test(){

        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'vex.meli.notices',
            method: 'get_data_from_meli',
            args: [],
            kwargs: {}
        });
        //this.state.dataPublications = datos['results']
        this.state.dataPublications = datos.results.map(item => ({
            ...item,
            formatted_date: this.formatDate(item.from_date), // nueva propiedad formateada
        }));

        console.log("get_data_from_meli",datos.results) ;

    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('es-PE', {
            year: 'numeric',
            month: 'long',
            day: '2-digit',
        });
    }

    async applyDateFilter(){

    }

    async handleFilterChange(){

    }
    mounted() {

    }

    onWillUnmount() {

    }


}

registry.category("actions").add("odoo-mercadolibre.notices", NoticesTemplate);


