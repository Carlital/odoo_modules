/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

const { Component, useEffect } = owl;
export class SettingsGeneralTemplate extends Component {
  static template = "vex_sync_mercado_libre.settings_general";
  setup() {
    useEffect(() => {
      console.log("Starting useEffect settings_general");
    });
  }
}

registry
  .category("actions")
  .add("vex_sync_mercado_libre.settings_general", SettingsGeneralTemplate);

