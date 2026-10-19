/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { Component, onWillStart, useEffect, useRef, onRendered, useState, toRaw } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { useModel } from "@web/model/model";
import { SIZES } from "@web/core/ui/ui_service";
import { useViewButtons } from "@web/views/view_button/view_button_hook";
import { useSetupView } from "@web/views/view_hook";
import { useDebugCategory } from "@web/core/debug/debug_context";
import { usePager } from "@web/search/pager_hook";
import { isX2Many } from "@web/views/utils";
import { registry } from "@web/core/registry";
const viewRegistry = registry.category("views");

const originalSetup = FormController.prototype.setup;
const originalEdit = FormController.prototype.edit;
const originalSaveButtonClicked = FormController.prototype.saveButtonClicked;
const originalDiscard = FormController.prototype.discard;


odoo.__DEBUG__ && console.log("Console log inside the patch function", FormController.prototype, "form_controller");

patch(FormController.prototype, {
    setup() {
        this.props.preventEdit = this.env.inDialog ? false : true;
        originalSetup.call(this);
    },


    async edit() {
        if (originalEdit) {
            await originalEdit.call(this);
        }

        if (this.model && this.model.root) {
            await this.model.root.switchMode("edit");
        } else {
            console.error('Model or model root is not defined');
        }
    },

    async saveButtonClicked(params = {}) {
            if (originalSaveButtonClicked) {
                await originalSaveButtonClicked.call(this, params);
            }

            if (!this.env.inDialog) {
                await this.model.root.switchMode("readonly");
            } else {
                this.model.actionService.doAction({ type: 'ir.actions.act_window_close' });
            }
    },

     async discard() {
        if (originalDiscard) {
            await originalDiscard.call(this);
        }

        if (!this.env.inDialog) {
            await this.model.root.switchMode("readonly");
        } else {
            this.model.actionService.doAction({ type: 'ir.actions.act_window_close' });
        }
    },

    async beforeLeave() {
        if (this.model.root.isDirty) {
            if (confirm("The changes you have made will save Automatically!")) {
                await this.model.root.save();
                return true;
            } else {
                return false;
            }
        }
        return true;
    }

})

