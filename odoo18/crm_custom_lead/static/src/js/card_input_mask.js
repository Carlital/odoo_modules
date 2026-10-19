/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CardInputMask extends Component {
    static template = "crm_custom_lead.CardInputMaskTemplate";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.inputRef = useRef("cardInput");
        this.state = useState({
            cardType: null,
            isValid: null, // null = sin validar, true = válido, false = inválido
        });

        onMounted(() => {
            this.detectCardType(this.props.record.data[this.props.name] || '');
        });
    }

    get inputValue() {
        return this.props.record.data[this.props.name] || '';
    }

    get cardTypeLabel() {
        const types = {
            'visa': 'Visa',
            'mastercard': 'Mastercard',
            'american_express': 'American Express',
            'diners_club': 'Diners Club',
            'discover': 'Discover',
            'jcb': 'JCB',
            'unionpay': 'UnionPay',
        };
        return this.state.cardType ? types[this.state.cardType] : null;
    }

    get cardTypeIcon() {
        const icons = {
            'visa': '💳',
            'mastercard': '💳',
            'american_express': '💳',
            'diners_club': '💳',
            'discover': '💳',
            'jcb': '💳',
            'unionpay': '💳',
        };
        return this.state.cardType ? icons[this.state.cardType] : '💳';
    }

    detectCardType(value) {
        if (!value) {
            this.state.cardType = null;
            return null;
        }

        const cleaned = value.replace(/\D/g, '');
        
        if (cleaned.startsWith('4')) {
            this.state.cardType = 'visa';
            return 'visa';
        } else if (/^(51|52|53|54|55)/.test(cleaned) || (cleaned.length >= 4 && parseInt(cleaned.substring(0, 4)) >= 2221 && parseInt(cleaned.substring(0, 4)) <= 2720)) {
            this.state.cardType = 'mastercard';
            return 'mastercard';
        } else if (/^(34|37)/.test(cleaned)) {
            this.state.cardType = 'american_express';
            return 'american_express';
        } else if (/^(6011|65|64[4-9]|622)/.test(cleaned)) {
            this.state.cardType = 'discover';
            return 'discover';
        } else if (/^(36|38|30[0-5])/.test(cleaned)) {
            this.state.cardType = 'diners_club';
            return 'diners_club';
        } else if (cleaned.startsWith('35')) {
            this.state.cardType = 'jcb';
            return 'jcb';
        } else if (cleaned.startsWith('62')) {
            this.state.cardType = 'unionpay';
            return 'unionpay';
        }
        
        this.state.cardType = null;
        return null;
    }

    validateLuhn(number) {
        if (!number || number.length < 13) {
            return null; // No validar si está incompleto
        }

        let suma = 0;
        let alternar = false;
        
        for (let i = number.length - 1; i >= 0; i--) {
            let digito = parseInt(number[i]);
            
            if (alternar) {
                digito *= 2;
                if (digito > 9) {
                    digito -= 9;
                }
            }
            
            suma += digito;
            alternar = !alternar;
        }
        
        return suma % 10 === 0;
    }

    async onInput(ev) {
        let value = ev.target.value;
        
        // Limpiar caracteres no numéricos
        const cleaned = value.replace(/\D/g, '');
        
        // Limitar a 19 dígitos
        const limited = cleaned.slice(0, 19);
        
        // Formatear con espacios cada 4 dígitos
        const formatted = limited.replace(/(.{4})/g, '$1 ').trim();
        
        // Actualizar input visualmente
        ev.target.value = formatted;
        
        // Detectar tipo de tarjeta
        const cardType = this.detectCardType(limited);
        
        // Validar solo si tiene entre 13 y 19 dígitos
        if (limited.length >= 13 && limited.length <= 19) {
            this.state.isValid = this.validateLuhn(limited);
        } else if (limited.length > 0) {
            this.state.isValid = null; // Incompleto
        } else {
            this.state.isValid = null;
            this.state.cardType = null;
        }
        
        // Actualizar modelo de Odoo (siempre con formato)
        await this.props.record.update({ 
            [this.props.name]: formatted,
            'tipo_tarjeta': cardType || false
        });
    }

    onKeyDown(ev) {
        const input = ev.target;
        const cleaned = input.value.replace(/\D/g, '');
        
        // Teclas permitidas
        const allowedKeys = [
            'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 
            'ArrowUp', 'ArrowDown', 'Home', 'End', 'Tab', 'Enter', 'Escape'
        ];
        
        // Permitir atajos con Ctrl/Cmd
        if (ev.ctrlKey || ev.metaKey) {
            return true;
        }
        
        // Permitir teclas de control
        if (allowedKeys.includes(ev.key)) {
            return true;
        }
        
        // Solo permitir números
        if (!/^\d$/.test(ev.key)) {
            ev.preventDefault();
            return false;
        }
        
        // Bloquear si ya llegó al límite
        const hasSelection = input.selectionStart !== input.selectionEnd;
        if (cleaned.length >= 19 && !hasSelection) {
            ev.preventDefault();
            return false;
        }
        
        return true;
    }

    async onPaste(ev) {
        ev.preventDefault();
        
        const pastedText = (ev.clipboardData || window.clipboardData).getData('text');
        const cleaned = pastedText.replace(/\D/g, '').slice(0, 19);
        const formatted = cleaned.replace(/(.{4})/g, '$1 ').trim();
        
        ev.target.value = formatted;
        
        const cardType = this.detectCardType(cleaned);
        
        if (cleaned.length >= 13 && cleaned.length <= 19) {
            this.state.isValid = this.validateLuhn(cleaned);
        } else {
            this.state.isValid = null;
        }
        
        await this.props.record.update({ 
            [this.props.name]: formatted,
            'tipo_tarjeta': cardType || false
        });
    }

    onBlur(ev) {
        // Al perder el foco, validar definitivamente
        const cleaned = ev.target.value.replace(/\D/g, '');
        if (cleaned.length > 0 && cleaned.length < 13) {
            this.state.isValid = false;
        } else if (cleaned.length >= 13 && cleaned.length <= 19) {
            this.state.isValid = this.validateLuhn(cleaned);
        }
    }
}

registry.category("fields").add("card_input_mask", {
    component: CardInputMask,
});