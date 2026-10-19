import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    async clickRefund(){
        this.dialog.add(TextInputPopup, {
            title: "Token Requerido",
            placeholder: "Coloque el pin",
            getPayload: async (code) => {
                code = code.trim();
                if (code !== "") {
                    const orderCount = await this.env.services.orm.call(
                        "pos.token",                  // modelo
                        "is_valid_token",    // nombre del método
                        [code,'refund'],   // ID de la sesión activa (como lista)
                    );
                    if(orderCount){
                        const order = this.pos.get_order();
                        const partner = order.get_partner();
                        const searchDetails = partner ? {
                            fieldName: "PARTNER",
                            searchTerm: partner.name
                        } : {};
                        this.pos.showScreen("TicketScreen", {
                            stateOverride: {
                                filter: "SYNCED",
                                search: searchDetails,
                                destinationOrder: order,
                                from_return:true
                            },
                        });
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
    async clickDiscount() {
        this.dialog.add(TextInputPopup, {
            title: "Token Requerido",
            placeholder: "Coloque el pin",
            getPayload: async (code) => {
                code = code.trim();
                if (code !== "") {
                    const orderCount = await this.env.services.orm.call(
                        "pos.token",                  // modelo
                        "is_valid_token",    // nombre del método
                        [code,'discount'],   // ID de la sesión activa (como lista)
                    );
                    if(orderCount){
                        return await super.clickDiscount(...arguments);
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
    async clickPricelist() {
        this.dialog.add(TextInputPopup, {
            title: "Token Requerido",
            placeholder: "Coloque el pin",
            getPayload: async (code) => {
                code = code.trim();
                if (code !== "") {
                    const orderCount = await this.env.services.orm.call(
                        "pos.token",                  // modelo
                        "is_valid_token",    // nombre del método
                        [code,'pricelist'],   // ID de la sesión activa (como lista)
                    );
                    if(orderCount){
                        return await super.clickPricelist(...arguments);
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

    

});
