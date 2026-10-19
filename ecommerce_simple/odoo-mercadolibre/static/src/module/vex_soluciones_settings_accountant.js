/** @odoo-module **/

import { Component, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class SettingsAccsountantTemplate extends Component {
  static template = "vex_sync_mercado_libre.settings_accountant";

  async setup() {}
}

registry
  .category("actions")
  .add("vex_sync_mercado_libre.settings_accountant", SettingsAccsountantTemplate);
