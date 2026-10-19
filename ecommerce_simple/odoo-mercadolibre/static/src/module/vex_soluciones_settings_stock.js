/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class SettingsStockTemplate extends Component {
  static template = "vex_sync_mercado_libre.settings_stock";

  async setup() {}
}

registry
  .category("actions")
  .add("vex_sync_mercado_libre.settings_stock", SettingsStockTemplate);
