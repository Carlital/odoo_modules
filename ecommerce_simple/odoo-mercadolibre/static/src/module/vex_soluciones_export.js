/** @odoo-module **/

import { Component, useState, useEffect, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class SettingsTemplate extends Component {
  static template = "vex_sync_mercado_libre.export";

  setup() {
    this.orm = useService("orm");
    this.state = useState({
      isSidebarVisible: false,
      subMenuSelected: "basicData", // Puede ser basicData, filters, accounts
      validInstances: [],
    });

    // Utilizando onMounted para asegurar que se ejecuta una vez después de que el componente está montado
    onMounted(async () => {
      const validInstances = await this.getValidInstances();
      this.state.validInstances = validInstances;
    });
  }

  toggleSidebar() {
    this.state.isSidebarVisible = !this.state.isSidebarVisible;
  }

  selectSubMenu(subMenu) {
    this.state.subMenuSelected = subMenu;
  }

  async getValidInstances() {
    const instances = await this.orm.call("vex.instance", "search_read", [
      [["store", "=", "mercadolibre"]],
    ]);
    console.log("valid instances", instances);
    return instances;
  }
}

registry.category("actions").add("vex_sync_mercado_libre.export", SettingsTemplate);
