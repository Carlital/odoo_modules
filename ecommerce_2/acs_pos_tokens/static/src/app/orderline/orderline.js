/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
// Componente OWL del POS que renderiza la línea (plantilla: point_of_sale.Orderline)
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";

patch(Orderline.prototype, {


    /**
     * Handler del click en el ícono de lápiz:
     * - Pide token con TextInputPopup
     * - Valida con método Python `pos.token.is_valid_token`
     * - Si válido, ejecuta navegación/acción (ejemplo: ir a TicketScreen con filtros)
     */
    async requestToken(ev) {
        
        if (this.env.services.pos.get_order().get_selected_orderline()) {
            let product_id = this.env.services.pos.get_order().get_selected_orderline().product_id.id;
            const existProductPrice = await this.env.services.orm.call(
                "pos.token",                  // modelo
                "get_token_with_price",    // nombre del método
                [product_id],   // ID de la sesión activa (como lista)
            );
            if (!existProductPrice) {
                this.env.services.dialog.add(AlertDialog, {
                    title: "Sin permiso",
                    body: "No se puede modificar el precio de este producto",
                });
                return;
            }else{
                this.env.services.dialog.add(TextInputPopup, {
                    title: "Token Requerido",
                    placeholder: "Coloque el pin",
                    getPayload: async (code) => {
                        code = code.trim();
                        if (code !== "") {
                            const orderCount = await this.env.services.orm.call(
                                "pos.token",                  // modelo
                                "is_valid_token",    // nombre del método
                                [code + "~" + product_id, 'price'],   // ID de la sesión activa (como lista)
                            );
                            if (orderCount) {
                            
                                this.env.services.number_buffer.capture();
                                this.env.services.number_buffer.reset();
                                this.env.services.pos.numpadMode = 'price';
                                return;
                            } else {
                                this.env.services.dialog.add(AlertDialog, {
                                    title: "Token Incorrecto",
                                    body: "El token ingresado no es correcto",
                                });
                                return;
                            }

                        } else {
                            this.env.services.dialog.add(AlertDialog, {
                                title: "Token Incorrecto",
                                body: "El token ingresado no es correcto",
                            });
                            return;
                        }
                    },
                });
            }
        }

    },
});
