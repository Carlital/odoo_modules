/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useChildRef } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class ExportDialog extends Component {
    setup() {
        this.env.dialogData.dismiss = () => this._cancel();
        this.modalRef = useChildRef();
        this.isProcess = false;
    }

    async _cancel() {
        return this.execButton(this.props.cancel);
    }

    async _confirm() {
        return this.execButton(this.props.confirm);
    }

    async _confirmHorizontal() {
        return this.execButton(this.props.confirmHorizontal);
    }

    setButtonsDisabled(disabled) {
        this.isProcess = disabled;
        if (!this.modalRef.el) {
            return;
        }
        for (const button of [...this.modalRef.el.querySelectorAll(".modal-footer button")]) {
            button.disabled = disabled;
        }
    }

    async execButton(callback) {
        if (this.isProcess) {
            return;
        }
        this.setButtonsDisabled(true);
        if (callback) {
            let shouldClose;
            try {
                shouldClose = await callback();
            } catch (e) {
                console.error("Error during execution:", e);
                this.props.close();
                throw e;
            }
            if (shouldClose === false) {
                this.setButtonsDisabled(false);
                return;
            }
        }
        this.props.close();
    }
}
ExportDialog.template = "ExportPdf.List";
ExportDialog.components = { Dialog };
ExportDialog.props = {
    close: Function,
    title: {
        validate: (m) => {
            return (
                typeof m === "string" || (typeof m === "object" && typeof m.toString === "function")
            );
        },
        optional: true,
    },
    body: String,
    confirm: { type: Function, optional: true },
    confirmHorizontal: { type: Function, optional: true },
    confirmHorizontalLabel: { type: String, optional: true },
    confirmLabel: { type: String, optional: true },
    confirmClass: { type: String, optional: true },
    cancel: { type: Function, optional: true },
    cancelLabel: { type: String, optional: true },
};
ExportDialog.defaultProps = {
    confirmLabel: _t("Export"),
    confirmHorizontalLabel: _t("Export Landscape"),
    cancelLabel: _t("Cancel"),
    confirmClass: "btn-primary",
    title: _t("Export PDF"),
};
