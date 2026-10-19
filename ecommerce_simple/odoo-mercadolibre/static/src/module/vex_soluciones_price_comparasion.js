/** @odoo-module **/

import { Component, useRef, onWillStart, useEffect } from "@odoo/owl";
import { loadBundle, loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class AutomaticPricingTemplate extends Component {
  static template = "vex_sync_mercado_libre.price_comparasion";

  async setup() {
    this.priceComparasionChartReference = useRef("priceComparasionChart");
    this.priceComparasionChartReference = null;

    onWillStart(async () => {
      console.log("Starting priceComparasionChart onWillStart");
      await loadBundle("web.chartjs_lib");
      await loadJS("vex_sync_mercado_libre/static/src/js/chart.umd.js");
    });

    useEffect(() => {
      console.log("Starting priceComparasionChart useEffect");
      this.renderPriceComparasionChart();
    });
  }

  renderPriceComparasionChart() {
    // pie chart render
    if (this.precioBajoChart) {
      this.precioBajoChart.destroy();
    }

    this.precioBajoChart = new Chart(this.precioBajoChartReference.el, {
      type: "bar",
      data: {
        labels: ["January", "February", "March", "April"],
        datasets: [
          {
            label: "Cheaper than the competition",
            data: [20, 20, 30, 10],
            // transparent purple
            backgroundColor: "rgb(210, 132, 232,0.4)",
            borderColor: "rgb(210, 132, 232,0.4)",
            tension: 0.1,
          },
          {
            label: "Market Price",
            data: [40, 20, 5, 10],
            // transparent red
            backgroundColor: "rgb(218, 241, 241)",
            borderColor: "rgb(218, 241, 241)",
            tension: 0.1,
          },
          {
            label: "More expensive than the competition",
            data: [30, 10, 5, 10],
            // transparent green
            backgroundColor: "rgb(251, 214, 231)",
            borderColor: "rgb(251, 214, 231)",
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Price Competitiveness",
            font: {
              size: 24,
            },
          },
        },
        maintainAspectRatio: false,
      },
    });
  }
}

registry
  .category("actions")
  .add("vex_sync_mercado_libre.price_comparasion", AutomaticPricingTemplate);
