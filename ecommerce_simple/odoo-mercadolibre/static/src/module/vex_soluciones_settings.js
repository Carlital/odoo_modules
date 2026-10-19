/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class SettingsTemplate extends Component {
  static template = "vex_sync_mercado_libre.settings";

  async setup() {
    this.state = useState({
      selectedMenuOption: "general",
      isSidebarVisible: true,
    });
  }

  selectMenuOption(option) {
    this.state.selectedMenuOption = option;
  }
}

registry
  .category("actions")
  .add("vex_sync_mercado_libre.settings", SettingsTemplate);
