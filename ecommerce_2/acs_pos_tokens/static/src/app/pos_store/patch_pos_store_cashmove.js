/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import {
    makeAwaitable,
    ask,
    makeActionAwaitable,
} from "@point_of_sale/app/store/make_awaitable_dialog";

patch(PosStore.prototype, {

    async closeSession() {
        this.dialog.add(TextInputPopup, {
            title: "Token Requerido",
            placeholder: "Coloque el pin",
            getPayload: async (code) => {
                code = code.trim();
                if (code !== "") {
                    const orderCount = await this.env.services.orm.call(
                        "pos.token",                  // modelo
                        "is_valid_token",    // nombre del método
                        [code,'cerrar_caja'],   // ID de la sesión activa (como lista)
                    );
                    if(orderCount){
                        const info = await this.getClosePosInfo();

                        if (info) {
                            this.dialog.add(ClosePosPopup, info);
                        }
                        return;
                    }else{
                        this.dialog.add(AlertDialog, {
                            title: "Token Incorrecto",
                            body: "El token ingresado no es correcto",
                        });
                        return;
                    }
                    
                }else{
                    this.dialog.add(AlertDialog, {
                        title: "Token Incorrecto",
                        body: "El token ingresado no es correcto",
                    });
                    return;
                }
            },
        });
        
        
    },

    async cashMove() {
       
        this.dialog.add(TextInputPopup, {
            title: "Token Requerido",
            placeholder: "Coloque el pin",
            getPayload: async (code) => {
                code = code.trim();
                if (code !== "") {
                    const orderCount = await this.env.services.orm.call(
                        "pos.token",                  // modelo
                        "is_valid_token",    // nombre del método
                        [code,'entrada_salida'],   // ID de la sesión activa (como lista)
                    );
                    if(orderCount){
                        await super.cashMove(...arguments);
                    }else{
                        this.dialog.add(AlertDialog, {
                            title: "Token Incorrecto",
                            body: "El token ingresado no es correcto",
                        });
                        return;
                    }
                    
                }else{
                    this.dialog.add(AlertDialog, {
                        title: "Token Incorrecto",
                        body: "El token ingresado no es correcto",
                    });
                    return;
                }
            },
        });
    },

    async showScreen(name, props) {
        if(name == 'TicketScreen'){
            if(props.stateOverride?.from_return === true){
                return await super.showScreen(...arguments);
            }
            this.dialog.add(TextInputPopup, {
                title: "Token Requerido",
                placeholder: "Coloque el pin",
                getPayload: async (code) => {
                    code = code.trim();
                    if (code !== "") {
                        const orderCount = await this.env.services.orm.call(
                            "pos.token",                  // modelo
                            "is_valid_token",    // nombre del método
                            [code,'ordenes'],   // ID de la sesión activa (como lista)
                        );
                        if(orderCount){
                            return await super.showScreen(...arguments);
                        }else{
                            this.dialog.add(AlertDialog, {
                                title: "Token Incorrecto",
                                body: "El token ingresado no es correcto",
                            });
                            return;
                        }
                        
                    }else{
                        this.dialog.add(AlertDialog, {
                            title: "Token Incorrecto",
                            body: "El token ingresado no es correcto",
                        });
                        return;
                    }
                },
            });
        }else{
            return await super.showScreen(...arguments);
        }
        

    }


});
