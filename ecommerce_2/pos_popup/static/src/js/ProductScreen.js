/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * Componente para el popup de modificación de cantidad
 */
export class QuantityPopup extends Component {
    static components = { Dialog };
    static props = {
        close: Function,
        product: Object,
        quantity: { type: Number, optional: true },
        onConfirm: Function,
    };

    // Definir la plantilla usando xml`` para Odoo 18
    static template = xml`
        <Dialog 
            title="'Cantidad de Producto'"
            contentClass="'p-4'"
            footer="false"
        >
            <div class="d-flex flex-column">
                <div class="product-name mb-3 text-center fw-bold">
                    <t t-esc="props.product.display_name"/>
                </div>
                
                <div class="quantity-control d-flex align-items-center justify-content-center mb-4">
                    <button class="btn btn-secondary" t-on-click="decrement">
                        <i class="fa fa-minus"/>
                    </button>
                    
                    <div class="mx-3 qty-input" style="width: 100px;">
                        <input 
                            class="form-control text-center" 
                            type="number" 
                            t-att-value="state.inputQty" 
                            t-on-input="onInputChange"
                            t-on-keydown="onInputKeyDown"
                            step="1"
                            min="1"
                            id="qty_input_field"
                        />
                    </div>
                    
                    <button class="btn btn-secondary" t-on-click="increment">
                        <i class="fa fa-plus"/>
                    </button>
                </div>
                
                <div class="text-center">
                    <button class="btn btn-primary" t-on-click="confirm">
                        Confirmar
                    </button>
                </div>
            </div>
        </Dialog>
    `;

    setup() {
        this.pos = usePos();
        this.state = useState({
            inputQty: this.props.quantity || 1,
        });

        // Respaldo de las funciones originales que queremos deshabilitar
        this.originalBarcodeScanListener = this.pos.barcodeReader?.barcodeScanned?.bind(this.pos.barcodeReader);
        // Backup del método de escape del diálogo
        this.originalOnKeydownListener = document.onkeydown;

        onMounted(() => {
            // Colocar el foco en el input y seleccionar su contenido
            this.focusInputField();

            // Desactivar el escáner de código de barras
            if (this.pos.barcodeReader) {
                this.pos.barcodeReader.barcodeScanned = () => { }; // Función vacía que no hace nada
            }

            // Deshabilitar la tecla escape y personalizar manejo de teclado a nivel global
            document.onkeydown = (evt) => {
                if (evt.key === 'Escape') {
                    evt.stopPropagation();
                    evt.preventDefault();
                    return false;
                }

                // Asegurarse de que el foco está siempre en el input
                const inputElement = document.getElementById('qty_input_field');
                if (document.activeElement !== inputElement) {
                    inputElement?.focus();
                }
            };

            // Manipulaciones del DOM para hacer el diálogo modal
            setTimeout(() => {
                // Ocultar la X del diálogo para forzar el uso del botón Confirmar
                const closeButtons = document.querySelectorAll('.modal-header .btn-close');
                closeButtons.forEach(button => {
                    button.style.display = 'none';
                });

                // Asegurar que el modal no se cierre al hacer clic fuera
                const modalBackdrops = document.querySelectorAll('.modal-backdrop');
                modalBackdrops.forEach(backdrop => {
                    backdrop.style.zIndex = '9999';

                    // Prevenir clic en el backdrop
                    backdrop.addEventListener('click', (e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        this.focusInputField();
                        return false;
                    });
                });

                // Asegurar que el modal esté por encima de todo
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modal => {
                    modal.style.zIndex = '10000';

                    // Al hacer clic en cualquier parte del modal, enfocar el input
                    modal.addEventListener('click', () => {
                        this.focusInputField();
                    });
                });

                // Ocultar el footer predeterminado del diálogo si existe
                const modalFooters = document.querySelectorAll('.modal-footer');
                modalFooters.forEach(footer => {
                    if (footer.querySelector('.btn-primary') &&
                        footer.querySelector('.btn-primary').textContent.trim() === 'Ok') {
                        footer.style.display = 'none';
                    }
                });

                // Forzar foco en el input
                this.focusInputField();
            }, 100); // pequeño timeout para asegurar que el DOM está listo
        });

        onWillUnmount(() => {
            // Restaurar el escáner de código de barras al cerrar
            if (this.pos.barcodeReader && this.originalBarcodeScanListener) {
                this.pos.barcodeReader.barcodeScanned = this.originalBarcodeScanListener;
            }

            // Restaurar el manejador de teclado original
            if (this.originalOnKeydownListener) {
                document.onkeydown = this.originalOnKeydownListener;
            }
        });
    }

    // Método para enfocar el input y seleccionar su contenido
    focusInputField() {
        setTimeout(() => {
            const inputElement = document.getElementById('qty_input_field');
            if (inputElement) {
                inputElement.focus();
                inputElement.select();
            }
        }, 50);
    }

    increment() {
        this.state.inputQty += 1;
        this.focusInputField();
    }

    decrement() {
        if (this.state.inputQty > 1) {
            this.state.inputQty -= 1;
        }
        this.focusInputField();
    }

    confirm() {
        if (this.state.inputQty <= 0) {
            return;
        }
        this.props.onConfirm(this.state.inputQty);
        this.props.close();
    }

    // Control de teclas permitidas
    onInputKeyDown(event) {
        const allowedKeys = [
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', // Números
            'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', // Teclas de control
            'Home', 'End' // Navegación
        ];

        // Si la tecla no está en la lista de permitidas, bloquearla
        if (!allowedKeys.includes(event.key)) {
            event.preventDefault();
            return false;
        }

        // Bloquear explícitamente la tecla Enter
        if (event.key === 'Enter') {
            event.preventDefault();
            return false;
        }
    }

    onInputChange(event) {
        const value = parseFloat(event.target.value);
        this.state.inputQty = !isNaN(value) && value > 0 ? value : 1;
    }
}

// Guardar referencia al método original
const originalAddLineToCurrentOrder = PosStore.prototype.addLineToCurrentOrder;

// Parche para el método addLineToCurrentOrder
patch(PosStore.prototype, {
    /**
     * @override
     */
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        console.log('Producto agregado al pedido:', vals.product_id?.display_name || vals.product_id);

        // Si no estamos en modo configuración o viene desde código de barras, no mostrar popup
        if (!configure || opts.code) {
            return await originalAddLineToCurrentOrder.call(this, vals, opts, configure);
        }

        // Mostrar el popup para modificar la cantidad
        return new Promise((resolve) => {
            // Configurar diálogo 
            const dialogProps = {
                product: vals.product_id,
                quantity: vals.qty || 1,
                onConfirm: async (quantity) => {
                    // Actualizar la cantidad en vals
                    vals.qty = quantity;
                    // Llamar al método original con la nueva cantidad
                    const result = await originalAddLineToCurrentOrder.call(this, vals, opts, configure);
                    resolve(result);
                },
            };

            // Añadir el diálogo
            this.dialog.add(QuantityPopup, dialogProps, {
                // Como fallback, si de alguna manera se cierra el diálogo
                // sin confirmar, aún así resolvemos con null (no se añade producto)
                onClose: () => {
                    resolve(null);
                }
            });
        });
    },
});