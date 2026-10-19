/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

export class WebDebug extends Component {
    static template = "web_debug.WKDebug";
    setup(){
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        onWillStart(async () => {
            this.is_employee = await this.orm.call("res.users", "has_group", ['base.group_system'])
            .then(function (is_employee){
                return is_employee;
            });  
          });
             
    }

    oe_activate_debug_mode(ev) {
        ev.preventDefault();
        var final = window.location.href.split('#')[1]
        let params = new URLSearchParams(window.location.search);
        params.set('debug', '1');
        var loc = window.location.pathname + '?' + params.toString() + '#' + final;
        // var src = window.location.protocol +"//"+ window.location.hostname + ":" + window.location.port + window.location.pathname + '?debug=1' + "#" + final;
        window.location=loc;
        console.log(loc);

    }


 
}


export const systrayDebug = {
    Component:WebDebug,
};

registry
    .category("systray")
    .add("web_debug.WKDebug", systrayDebug, { sequence: 10 });




// odoo.define('web_debug.debug', function(require) {
//     "use strict";

//     var core = require('web.core');
//     var mixins = require('web.mixins');
//     var rpc = require('web.rpc');
//     var Session = require('web.Session');
//     var QWeb = core.qweb;
//     var _t = core._t;
//     var SystrayMenu = require('web.SystrayMenu');
//     var Widget = require('web.Widget');

//     var WKDebug = Widget.extend({
//         template: 'WKDebug',
//         events: {
//             "click .oe_activate_debug_mode": "oe_activate_debug_mode",
//         },
//         oe_activate_debug_mode: function(event) {
//             event.preventDefault();
//             window.location = $.param.querystring(window.location.href, 'debug=1');
//         },
//     });
    
//     rpc.query({
//         model: 'res.users',
//         method: 'has_group',
//         args: ['base.group_system']
//     })
//     .then(function(is_employee) {
//         console.log(is_employee);
//         if (is_employee) {
//             SystrayMenu.Items.push(WKDebug);
//         }
//     });
// });
