/** @odoo-module */

import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";


export class OrderCountComponent extends Component {
    static template = "acs_pos_count_global.OrderCountComponent";
    static props = {};

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.orderCount = 0;
        onWillStart(async () => {
            const orderCount = await this.orm.call(
                "pos.order",                  // modelo
                "compute_all_order_count",    // nombre del método
                [],   // ID de la sesión activa (como lista)
                {}                             // kwargs si necesitas
            );
            this.orderCount = orderCount;
        });
        this.pos.data.connectWebSocket("ACS_POS_COUNT_GLOBAL", this._onNotification.bind(this));
    }
    _onNotification(data) {
        var config_id = data['config_id'];
        var count = data['count'];
        if(this.pos.config.id == config_id){
            this._handleNotification(count);
        }
        
    }
    
    async _handleNotification(count) {
        this.orderCount = count;
        this.render();
        
    }
}