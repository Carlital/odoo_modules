/** @odoo-module **/

import { Component, useRef, onWillStart, useEffect } from "@odoo/owl";
import { loadBundle, loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

class AutomaticPricingTemplate extends Component {
  static template = "vex_sync_mercado_libre.automatic_pricing";

  async setup() {
    this.precioBajoChartReference = useRef("precioBajoChart");
    this.precioIgualChartReference = useRef("precioIgualChart");
    this.precioAltoChartReference = useRef("precioAltoChart");

    this.precioBajoChart = null;
    this.precioIgualChart = null;
    this.precioAltoChart = null;

    onWillStart(async () => {
      await loadBundle("web.chartjs_lib");
      await loadJS("vex_sync_mercado_libre/static/src/js/chart.umd.js");
    });

    useEffect(() => {
      this.renderPrecioBajoChart();
      this.renderPrecioIgualChart();
      this.renderPrecioAltoChart();
    });
  }

  renderPrecioBajoChart() {
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

  renderPrecioIgualChart() {
    // pie chart render
    if (this.precioIgualChart) {
      this.precioIgualChart.destroy();
    }

    this.precioIgualChart = new Chart(this.precioIgualChartReference.el, {
      type: "doughnut",
      data: {
        labels: ["Competitive Price", "Market Price", "Non-competitive Price"],
        datasets: [
          {
            label: "Prices",
            data: [20, 20, 30],
            // transparent blue
            backgroundColor: [
              "rgb(210, 132, 232,0.4)",
              "rgb(218, 241, 241)",
              "rgb(251, 214, 231)",
            ],
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Margin by Category", // Título principal
            font: {
              size: 24, // Tamaño del texto del título
            },
          },
        },
      },
    });
  }

  renderPrecioAltoChart() {
    // pie chart render
    if (this.precioAltoChart) {
      this.precioAltoChart.destroy();
    }

    this.precioAltoChart = new Chart(this.precioAltoChartReference.el, {
      type: "line",
      data: {
        labels: ["January", "February", "March", "April"],
        datasets: [
          {
            label: "Magin by Category",
            data: [20, 40, 60, 80],
            backgroundColor: "rgb(141, 152, 255,0.2)",
            borderColor: "rgb(141, 152, 255)",
            tension: 0.1,
          },
          {
            label: "Price evolution",
            data: [40, 60, 80, 100],
            backgroundColor: "rgb(157, 97, 174,0.2)",
            borderColor: "rgb(157, 97, 174)",
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Price and Margin Evolution", // Título principal
            font: {
              size: 24, // Tamaño del texto del título
            },
          },
        },
        maintainAspectRatio: false,
        scales: {
          y: {
            stacked: true,
            grid: {
              display: true,
              color: "rgba(255,99,132,0.2)",
            },
          },
          x: {
            grid: {
              display: false,
            },
          },
        },
      },
    });
  }
}

registry
  .category("actions")
  .add("vex_sync_mercado_libre.automatic_pricing", AutomaticPricingTemplate);
