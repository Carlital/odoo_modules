/** @odoo-module **/

import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { archParseBoolean } from "@web/views/utils";
import { STATIC_ACTIONS_GROUP_NUMBER } from "@web/search/action_menus/action_menus";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";
import { ExportDialog } from "../js/export_dialog";
import { Component } from "@odoo/owl";

const cogMenuRegistry = registry.category("cogMenu");

/**
 * 'Export PDF' menu
 *
 * Este componente se utiliza para exportar en PDF los registros de un modelo específico.
 * @extends Component
 */
export class ExportPdf extends Component {
    static template = "web.ExportPdf";
    static components = { DropdownItem };

    // Método que define la funcionalidad al hacer clic en el menú de exportación PDF
    async onDirectExportPdf() {
        this.env.searchModel.trigger("direct-export-pdf");
        const component = this.__owl__.parent.parent.parent.parent.parent.component;

        const fields = component.props.archInfo.columns
            .filter((col) => col.type === "field")
            .map((col) => component.props.fields[col.name]);

        const exportField = [];
        const exportedFields = fields.map((field) => ({
            name: field.name,
            label: field.label || field.string,
        }));

        const resIds = await component.getSelectedResIds() || [];

        component.dialogService.add(ExportDialog, {
            title: _t("Export PDF"),
            context: exportedFields,
            confirm: () => this._exportData(exportField, resIds, component, "portrait"),
            confirmHorizontal: () => this._exportData(exportField, resIds, component, "landscape"),
            cancel: () => {},
        });
    }

    _exportData(exportField, resIds, component, orientation) {
        let checkboxes = document.querySelectorAll(`#check input[type="checkbox"]`);
        checkboxes.forEach((item) => {
            if (item.checked) {
                exportField.push({ name: item.name, label: item.value });
            }
        });
        const length_field = Array.from(Array(exportField.length).keys());

        jsonrpc("/get_data", {
            model: component.model.root.resModel,
            res_ids: resIds,
            fields: exportField,
            grouped_by: component.model.root.groupBy,
            context: component.props.context,
            domain: component.model.root.domain,
            orientation: orientation,
        }).then((data) => {
            const action = {
                type: "ir.actions.report",
                report_type: "qweb-pdf",
                paperformat_id: data.paperformat_id,
                report_name: data.report_name,
                data: { length: length_field, record: data },
            };
            return component.model.action.doAction(action);
        }).catch((error) => {
            console.error("Error in export:", error);
        });
    }
}

export const exportPdfItem = {
    Component: ExportPdf,
    groupNumber: STATIC_ACTIONS_GROUP_NUMBER,
    isDisplayed: async (env) =>
        env.config.viewType === "list" &&
        !env.model.root.selection.length &&
        await env.model.user.hasGroup("base.group_allow_export") &&
        archParseBoolean(env.config.viewArch.getAttribute("export_xlsx"), true),
};
cogMenuRegistry.add("export-pdf-menu", exportPdfItem, { sequence: 10 });
