/** @odoo-module **/

import { loadBundle, loadJS } from "@web/core/assets";
import { Component, onWillUnmount, useEffect, useRef, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


class ForecastTemplate extends Component {
    static template = "odoo-mercadolibre.forecast";

    setup() {
        this.rpc = useService("rpc");  // Using the RPC service
        this.action = useService("action");  // Using the Action service to open the view

        self = this.action; // Ensure self is set in the constructor

        this.http = useService("http");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");
        this.state = useState({
            title: "",
            description: "",
            segments: [],
            selectedSegment: null,
            searchText: '',
            filteredProducts: [],
            selectedProduct: null,
            column: "",

            showModal: false,

            items: [
            ]
        });        
        this.canvasSale = useRef('ForecastSales')
        this.chartSale= null
        this.canvasStock = useRef('ForecastStock')
        this.chartStock= null
        this.canvasCustomer = useRef('ForecastCustomers')
        this.chartCustomer= null

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js")
        });

        onMounted(async () => {
            const instances = await this.orm.searchRead("vex.instance", [
                ["license_valid_str", "=", "active"],
                ["store_type", "=", "mercadolibre"],
            ], ["id"]);
            if (instances.length === 0) {
                this.state.showModal = true;
            } else {
                this.state.showModal = false;
            }
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.forEach(function (tooltipTriggerEl) {
                    new bootstrap.Tooltip(tooltipTriggerEl);
                });
          });   
        useEffect(() => {
            const grid = GridStack.init({
                cellHeight: 'auto',
                animate: false, // show immediate (animate: true is nice for user dragging though)
            }).on('change', (ev, gsItems) => {
                this.column = grid.getColumn();
                console.log(this.column)
                console.log("actializado");
            });


            this.renderSalesChart(this.state.selectedProduct);
            this.renderStockChart(this.state.selectedProduct);
            this.renderCustomerChart(this.state.selectedProduct);
            this.get_initial_data()


            grid.load(this.state.items);

        }, () => []);               
    }
    async get_initial_data() {
        var limit = 20;  // Example limit value
        let topSellingProducts = await this.rpc('/web/dataset/call_kw', {
            model: 'product.template',
            method: 'get_top_selling_products',
            args: [limit],
            kwargs: {}
        });
        console.log('Productos más vendidos UPDATED:', topSellingProducts);


        this.products = topSellingProducts
        //this.state.selectedProduct = this.products[0].product_id;
        console.log("Eligiendo el primer valor");

        // Encuentra el input y establece el placeholder al producto seleccionado
        const searchInput = document.getElementById('productSearch'); // Usa document.getElementById en lugar de this.el.querySelector
        //const productName = this.getProductNameById(this.products[0].product_id);
        searchInput.placeholder = 'Seleccione un producto a predecir';
        //searchInput.placeholder = productName
        searchInput.value = '';

        //const titleElement = document.getElementById('tableTitle');
        // Change the text content of the title element
        //titleElement.textContent = 'Your New Table Name Here';

        //this.forecast_product(this.products[0].product_id);

        //this.calculateTableData();


    }        
    getProductNameById(id) {
        // Directamente accede a this.products (que es el estado)
        const product = this.products.find(product => product.product_id == id);
        return product ? product.product_name : null; // Devuelve el nombre o null si no se encuentra
    }  
    async updateChartData() {
        // Actualiza las ventas históricas y pronósticos del producto seleccionado       
        this.renderSalesChart(this.state.selectedProduct)
        this.renderStockChart(this.state.selectedProduct)
        this.renderCustomerChart(this.state.selectedProduct)
        //this.chartSale.update();
    }      
    onProductChange(event) {
        this.state.selectedProduct = event.target.value;
        console.log("Producto seleccionado:", this.state.selectedProduct);
        const productName = this.getProductNameById(this.state.selectedProduct);
        console.log("Nombre,", productName);

        // Encuentra el input y establece el placeholder al producto seleccionado
        const searchInput = document.getElementById('productSearch'); // Usa document.getElementById en lugar de this.el.querySelector
        searchInput.placeholder = productName
        searchInput.value = '';
        // Oculta la lista de autocompletado
        this.state.filteredProducts = [];

        // Llama a updateChartData para actualizar el gráfico con datos correspondientes
        this.updateChartData();
        let product_id = parseInt(this.state.selectedProduct, 10)


       // this.forecast_product(product_id);

    }   
    onSearchInput(ev) {
        const searchText = ev.target.value.toLowerCase();
        this.state.filteredProducts = this.products.filter(product =>
            product.product_name.toLowerCase().includes(searchText)
        );
    } 
    async renderSalesChart(productId) {
        console.log("productId", productId)
        if (productId) {
            
        
            console.log('Renderizando Grafico de Forecast Sale')
            const result = await this.rpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'get_sales_forecast_data',
                args: [[parseInt(productId)]],
                kwargs: {},
            });
            console.log("result", result)

            if (this.chartSale) {
                this.chartSale.destroy();
            }
            this.chartSale = new Chart(this.canvasSale.el, {
                type: 'line',
                data: {
                    labels: result.labels,
                    datasets: result.datasets.map(ds => ({
                        label: ds.label,
                        data: ds.data,
                        fill: false,
                        borderColor: ds.borderColor,
                        borderDash: ds.borderDash || [],
                        tension: 0.1,
                        pointBackgroundColor: ds.borderColor,
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Cantidad Vendida'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Fecha'
                            }
                        }
                    }
                }
            });
        }
    }

    async renderStockChart(productId) {
        if (productId) {
            console.log('Renderizando Grafico de Forecast Stock')
            const result = await this.rpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'get_stock_forecast_data',
                args: [[parseInt(productId)]],
                kwargs: {},
            });
            console.log("result", result)

            if (this.chartStock) {
                this.chartStock.destroy();
            }
            this.chartStock = new Chart(this.canvasStock.el, {
                type: 'line',
                data: {
                    labels: result.labels,
                    datasets: result.datasets.map(ds => ({
                        label: ds.label,
                        data: ds.data,
                        fill: false,
                        borderColor: ds.borderColor,
                        borderDash: ds.borderDash || [],
                        tension: 0.1,
                        pointBackgroundColor: ds.borderColor,
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Cantidad Vendida'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Fecha'
                            }
                        }
                    }
                }
            });
        }
    }

    async renderCustomerChart(productId) {
        if (productId) {
            console.log('Renderizando Grafico de Forecast Customer')
            const result = await this.rpc('/web/dataset/call_kw', {
                model: 'sale.order',
                method: 'get_customer_forecast_data',
                args: [[parseInt(productId)]],
                kwargs: {},
            });
            console.log("result", result)

            if (this.chartCustomer) {
                this.chartCustomer.destroy();
            }
            if (this.chartCustomer) {
                this.chartCustomer.destroy();
            }
            this.chartCustomer = new Chart(this.canvasCustomer.el, {
                type: 'line',
                data: {
                    labels: result.labels,
                    datasets: result.datasets.map(ds => ({
                        label: ds.label,
                        data: ds.data,
                        fill: false,
                        borderColor: ds.borderColor,
                        borderDash: ds.borderDash || [],
                        tension: 0.1,
                        pointBackgroundColor: ds.borderColor,
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'right'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Cantidad Vendida'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Fecha'
                            }
                        }
                    }
                }
            });
        }
    }

    async exportForecastExcel() {
        /* const action = await this.rpc('/export/forecast/excel');
        if (action && action.url) {
            window.location.href = action.url;
        } */
       window.open('/export/forecast/excel', '_blank');
    }
}
registry.category("actions").add("odoo-mercadolibre.forecast", ForecastTemplate);
