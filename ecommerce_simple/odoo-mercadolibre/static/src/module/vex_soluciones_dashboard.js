/** @odoo-module **/

import { loadBundle, loadJS, loadJSON } from "@web/core/assets";
import { Component, onWillUnmount, useEffect, useRef, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";
//import Chart from "chart.js/auto";




class Welcome extends Component {
    static template = "odoo-mercadolibre.welcome";

    setup() {
        
        //Code to open view
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
            orders_number: 200,
            total_orders: 100,
            new_customers_last_month: 0,
            total_customers_count: 0,
            products_count: 0,
            questions_count : 0,
            top_clients_data :[],
            top_products_data : [],
            latest_orders :[],
            chart_customers_evolution : [],
            monthly_profit_last_6_months : [],
            average_custom_order :[],
            top_5_categories_data :[],
            CompletedAndCanceled4months_data : [],
            get_sales_by_channel_last_5_months_data : [],
            question_count_by_category_data : [],

            showModal: false,

            text : "siuu",
            selectedSegment: null,
            column: "",
            items: [
                // { w: 2, h: 2, content: 'my first widget' }, 
                // { w: 2, content: 'another longer widget!' } 
            ]

        });
        
        this.canvasRef = useRef("productosSincronizadosChart");
        this.canvasRef2 = useRef("categoriasProductosChart");
        this.canvasRef3 = useRef("pie1");
        this.canvasRef4 = useRef("line1");
        this.canvasRef5 = useRef("bar1");
        this.canvasRef6 = useRef("radar1");
        this.canvasRef7 = useRef("doughnut1");
        this.canvasRef8 = useRef("polarArea1");
        this.canvasRef9 = useRef("bubble1");
        this.chart = null;
        this.chart2 = null;
        this.chart3 = null;
        this.chart4 = null;
        this.chart5 = null;
        this.chart6 = null;
        this.chart7 = null;
        this.chart8 = null;
        this.chart9 = null;
               

        onWillStart(async () => {           
            await loadBundle("web.chartjs_lib");
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js")
            /* const response = await fetch('/odoo-mercadolibre/static/src/module/data2.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            } */
            //const jsonData = await response.json();  // <-- Aquí es donde lo transformas
            const jsonData = await this.rpc("/web/dataset/call_kw", {
                model: "vex.dashboard.record",
                method: "generate_json_dashboard",
                args: [[]],
                kwargs: {},
            });
            console.log("Dashboard JSON:", jsonData);
            this.state.segments = jsonData.segments || [];

            this.state.orders_number = jsonData.orders_synced_today || 0;
            this.state.total_orders = jsonData.total_orders || 0;
            this.state.new_customers_last_month = jsonData.new_customers_last_month || 0;
            this.state.total_customers_count = jsonData.total_customers || 0;
            this.state.products_count = jsonData.total_products || 0;
            this.state.questions_count = jsonData.total_questions || 0;

            this.state.top_clients_data = jsonData.top_clients || [];
            this.state.top_products_data = jsonData.top_products || [];
            this.state.latest_orders = jsonData.recent_orders || [];

            this.state.chart_customers_evolution = jsonData.customers_evolution || [];
            this.state.monthly_profit_last_6_months = jsonData.total_earnings || [];
            this.state.average_custom_order = jsonData.average_customer_order || [];

            this.state.top_5_categories_data = jsonData.top_categories_sold || [];
            this.state.CompletedAndCanceled4months_data = jsonData.completed_and_canceled || [];
            this.state.get_sales_by_channel_last_5_months_data = jsonData.sales_distribution_by_channel || [];
            this.state.question_count_by_category_data = jsonData.questions || [];

            this.addBackground()

            console.log("Dashboard actualizado con éxito");
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
                // aquí podrías cargar el contenido principal del módulo si deseas
            }
        });

        useEffect(() => {
            const grid = GridStack.init({
                cellHeight: 'auto',
                animate: false, // show immediate (animate: true is nice for user dragging though)
                // columnOpts: {
                //     columnWidth: 100, // wanted width
                // },
            }).on('change', (ev, gsItems) => {
                this.column = grid.getColumn();
                console.log(this.column)
            });;

            this.renderChart();
            this.renderChart2();
            this.renderChart3();
            this.renderChart4();
            this.renderChart5();
            this.renderChart6();
            this.renderChart7();
            this.renderChart8();
            this.renderChart9();


            grid.load(this.state.items);

            this.load_data();

        },() => []    
            );


        onWillUnmount(() => {
            this.onWillUnmount()
            this.delBackground()
        });

        //this.load_data();
    }

    redirigirAConfiguracion() {
        this.action.doAction("vex_syncronizer.vex_sync_store_open_instances");
    }

    // Load dashboard data

     async load_data(){
        // this.fetchOrdersSyncedToday();
        // this.fetchTotalOrders();
        // this.fetchNewCustomersLastMonth();
        // this.fetchTotalCustomersCount();
        // this.fetchTotalProductsCount();
        // this.fectNewCustomerLastSixMonths();
        // this.fetchMonthlyProfitLastSixMonths();
        // this.fetchTopClients();
        // this.fetchTopProducts();
        // this.fetchLatestOrders();
        // this.get_average_custom_order_last_6_months();
        // this.top_5_categories();
        // this.CompletedAndCanceled4months();
        // this.get_sales_by_channel_last_5_months();
        // this.get_questions_count();
        // this.question_count_by_category();



        this.render();

        
    }

    async fetchOrdersSyncedToday(){
        let number = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'orders_synced_today',
            args: [],
            kwargs: {}
        });
        this.state.orders_number = jsonData.orders_synced_today;
    }

    async fetchTotalOrders (){
        let number = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_total_orders_count',
            args: [],
            kwargs: {}
        });
        this.state.total_orders = number;
    }

    async fetchNewCustomersLastMonth (){
        let number = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_new_customers_first_purchase_this_month',
            args: [],
            kwargs: {}
        });
        this.state.new_customers_last_month = number;
        
    }

    async fetchTotalCustomersCount (){
        let number = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'count_customers_with_server_meli',
            args: [],
            kwargs: {}
        });
        this.state.total_customers_count = number;        
    }

    async fetchTotalProductsCount (){
        let number = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_total_products',
            args: [],
            kwargs: {}
        });
        this.state.products_count = number;        
    }

    async fectNewCustomerLastSixMonths (){
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_or_update_new_customers_data',
            args: [],
            kwargs: {}
        });
        this.state.chart_customers_evolution = datos;   
        // Extraer etiquetas (meses) y datos (nuevos clientes) para el gráfico
        console.log("Los datos",datos) ;
        this.renderChart();
        this.chart.update();
    


    }

    async fetchMonthlyProfitLastSixMonths (){
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_monthly_profit_last_6_months',
            args: [],
            kwargs: {}
        });

        this.state.monthly_profit_last_6_months = datos;  
        console.log("DATOS",datos) ;
        this.renderChart4();
        this.chart4.update();

    }
    

    async fetchTopClients (){
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_top_clients_all_time',
            args: [],
            kwargs: {}
        });
        
        console.log("Topclients",datos) ;
        this.state.top_clients_data = datos;                       
    }

    async fetchTopProducts (){
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_top_products_all_time',
            args: [],
            kwargs: {}
        });
        

        if (typeof datos === "string") {
            console.log("Es una cadena:", datos);
        } else if (Array.isArray(datos)) {
            console.log("Es un array:", datos);
        } else {
            console.log("No es ni una cadena ni un array.");
        }

        
        console.log("TopProducts",datos) ;        
        this.state.top_products_data = datos;


    }

    async fetchLatestOrders (){
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_latest_orders',
            args: [],
            kwargs: {}
        });
        
        console.log("Latest Orders",datos) ;
        this.state.latest_orders = datos;                       
    }

    async get_average_custom_order_last_6_months(){
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_average_custom_order_last_6_months',
            args: [],
            kwargs: {}
        });
        
        console.log("get_average_custom_order_last_6_months",datos) ;
        this.state.average_custom_order = datos;  

        this.renderChart9();
        this.chart9.update();

    }
    

    async top_5_categories(){
        console.log("top_categories") ;
        
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_top_categories',
            args: [],
            kwargs: {}
        });
        
        console.log("top_categories",datos) ;
        this.state.top_5_categories_data = datos; 
        

        this.renderChart3();
        this.chart3.update();
        
    }

    


    async CompletedAndCanceled4months(){
        console.log("counts_last_4_months") ;
        
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_monthly_order_status_counts_last_4_months',
            args: [],
            kwargs: {}
        });
        
        console.log("counts_last_4_months",datos) ;
        this.state.CompletedAndCanceled4months_data = datos;
        
        

        this.renderChart5();
        this.chart5.update();
        
    }


    

    async get_sales_by_channel_last_5_months(){

        console.log("get_sales_by_channel_last_5_months") ;
        
        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'sale.order',
            method: 'get_sales_by_channel_last_5_months',
            args: [],
            kwargs: {}
        });
        
        console.log("get_sales_by_channel_last_5_months",datos) ;
        this.state.CompletedAndCanceled4months_data = datos;
        
        

        this.renderChart2();
        this.chart2.update();
        
    }

    async get_questions_count(){

        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'vex.meli.questions',
            method: 'get_question_count',
            args: [],
            kwargs: {}
        });
        
        console.log("get_question_count",datos) ;
        this.state.questions_count = datos;

    }


    

    async question_count_by_category(){

        let datos = await this.rpc('/web/dataset/call_kw', {
            model: 'vex.meli.questions',
            method: 'get_questions_count_by_category',
            args: [],
            kwargs: {}
        });
        
        console.log("question_count_by_category_data",datos) ;
        this.state.question_count_by_category_data = datos;

        this.renderChart8();
        this.chart8.update();

    }


    // Other code

    async today_orders() {
        this.notificationService.add("Abriendo órdenes de hoy", { type: 'info' });

        try {
            this.action.doAction("odoo-mercadolibre.action_order_tree_meli_today");
        } catch (err) {
            console.error("Error al abrir la vista:", err);
            this.notificationService.add("Error al abrir la vista", { type: 'danger' });
        }
    }
    
    async total_orders_views() {
        this.notificationService.add("Abriendo todas las órdenes", { type: 'info' });
        try {
            this.action.doAction("odoo-mercadolibre.action_order_tree_meli_all");
        } catch (err) {
            console.error("Error al abrir la vista:", err);
            this.notificationService.add("Error al abrir la vista", { type: 'danger' });
        }
    }
    async sync_now() {
        this.notificationService.add("Syncing Dashboard", { type: 'info' });
        try {
            await this.rpc("/web/dataset/call_kw", {
                model: "vex.dashboard.record",
                method: "generate_dashboard_record_daily",
                args: [],
                kwargs: {},
            });
            this.notificationService.add("Dashboard actualizado correctamente", { type: 'success' });

            // Opcional: esperar unos milisegundos para que se vea la notificación
            setTimeout(() => {
                window.location.reload();
            }, 800);  // puedes ajustar el tiempo si quieres

        } catch (error) {
            this.notificationService.add("Error al actualizar el dashboard", { type: 'danger' });
            console.error("Error al llamar generate_dashboard_record_daily:", error);
        }
    }





    async customers_view(){
        this.notificationService.add("Abriendo vista customers", { type: 'info' });

        // Code
        try {
            // Fetch the action related to the Sale Order
            

            this.rpc("/web/action/load", { action_id: "sale.action_orders" })
            .then((result) => {  // Change to arrow function to preserve 'this'
                const treeView = result.views.find((v) => v[1] === "list");
                console.log(result);
                // Open view with owl action service
                this.action.doAction({
                    name: 'Customers',
                    type: 'ir.actions.act_window',
                    res_model: 'res.partner',
                    target: 'current',
                    domain: [], // Specify your domain if needed
                    views: [[false, 'list']], // Use the tree view for the order list
                });
            })
            .catch((error) => {
                console.log(error);
                throw error;
            });
            
        } catch (error) {
            console.error("Error opening the Sale Orders view:", error);
        }

    }



    async open_client_view(){
        this.notificationService.add("Abriendo vista client", { type: 'warning' });

        // Code
        try {
            // Fetch the action related to the Sale Order
            

            this.rpc("/web/action/load", { action_id: "sale.action_orders" })
            .then((result) => {  // Change to arrow function to preserve 'this'
                const treeView = result.views.find((v) => v[1] === "list");
                console.log(result);
                // Open view with owl action service
                this.action.doAction({
                    name: 'Client',
                    type: 'ir.actions.act_window',
                    res_model: 'res.partner',
                    res_id: 888,
                    target: 'new',
                    domain: [], // Specify your domain if needed
                    views: [[false, 'form']], // Use the tree view for the order list
                });
            })
            .catch((error) => {
                console.log(error);
                throw error;
            });
            
        } catch (error) {
            console.error("Error opening the Sale Orders view:", error);
        }

    }

    async open_order_view(){
        this.notificationService.add("Abriendo vista client", { type: 'warning' });

        // Code
        try {
            // Fetch the action related to the Sale Order
            

            this.rpc("/web/action/load", { action_id: "sale.action_orders" })
            .then((result) => {  // Change to arrow function to preserve 'this'
                const treeView = result.views.find((v) => v[1] === "list");
                console.log(result);
                // Open view with owl action service
                this.action.doAction({
                    name: 'Order',
                    type: 'ir.actions.act_window',
                    res_model: 'sale.order',
                    res_id: 888,
                    target: 'new',
                    domain: [], // Specify your domain if needed
                    views: [[false, 'form']], // Use the tree view for the order list
                });
            })
            .catch((error) => {
                console.log(error);
                throw error;
            });
            
        } catch (error) {
            console.error("Error opening the Sale Orders view:", error);
        }

    }

    async open_product_view(){
        this.notificationService.add("Abriendo vista client", { type: 'warning' });

        // Code
        try {
            // Fetch the action related to the Sale Order
            

            this.rpc("/web/action/load", { action_id: "sale.action_orders" })
            .then((result) => {  // Change to arrow function to preserve 'this'
                const treeView = result.views.find((v) => v[1] === "list");
                console.log(result);
                // Open view with owl action service
                this.action.doAction({
                    name: 'Product',
                    type: 'ir.actions.act_window',
                    res_model: 'product.template',
                    res_id: 888,
                    target: 'new',
                    domain: [], // Specify your domain if needed
                    views: [[false, 'form']], // Use the tree view for the order list
                });
            })
            .catch((error) => {
                console.log(error);
                throw error;
            });
            
        } catch (error) {
            console.error("Error opening the Sale Orders view:", error);
        }

    }

    async products_view(){
        this.notificationService.add("Abriendo vista productos", { type: 'info' });

        // Code
        try {
            // Fetch the action related to the Sale Order
            

            this.rpc("/web/action/load", { action_id: "sale.action_orders" })
            .then((result) => {  // Change to arrow function to preserve 'this'
                const treeView = result.views.find((v) => v[1] === "list");
                console.log(result);
                // Open view with owl action service
                this.action.doAction({
                    name: 'Products',
                    type: 'ir.actions.act_window',
                    res_model: 'product.template',
                    target: 'current',
                    domain: [], // Specify your domain if needed
                    views: [[false, 'kanban']],// Use the tree view for the order list
                });
            })
            .catch((error) => {
                console.log(error);
                throw error;
            });
            
        } catch (error) {
            console.error("Error opening the Sale Orders view:", error);
        }

    }

    async questions_view() {
        this.notificationService.add("Abriendo vista questions", { type: 'info' });
    
        try {
            // Llamamos directamente al XML ID de la acción cliente
            const action = await this.rpc("/web/action/load", {
                action_id: "odoo-mercadolibre.action_open_chatbot"
            });
    
            // Ejecutamos la acción cliente
            this.action.doAction(action);
        } catch (error) {
            console.error("Error al abrir vista questions:", error);
        }
    }


    addBackground() {
        const actionManagerEl = document.querySelector('.o_action_manager');
        if (actionManagerEl) {
            actionManagerEl.id = 'doodles';
            actionManagerEl.classList.add('list-contact');
        } else {
            console.warn('Elemento .o_action_manager no encontrado.');
        }
    }

    delBackground() {
        const actionManagerEl = document.querySelector('.o_action_manager');
        if (actionManagerEl.id = 'doodles') {
            actionManagerEl.id = null;
            actionManagerEl.classList.remove('list-contact');
        } else {
            console.warn('Elemento .o_action_manager no encontrado.');
        }
    }
        
    

    selectSegment(ev) {
        this.state.selectedSegment = this.state.segments.find(segment => segment.id == ev.target.value);
        console.log(this.state);
    }

renderChart() {
    if (this.chart) {
        this.chart.destroy();
    }

    const data = this.state.chart_customers_evolution;

    if (!data || !data.labels || !Array.isArray(data.datasets)) {
        console.warn("Formato inválido en 'chart_customers_evolution'");
        return;
    }

    this.chart = new Chart(this.canvasRef.el, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, index) => ({
                label: ds.label || `Serie ${index + 1}`,
                data: ds.data || [],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Customers Evolution',
                    font: {
                        size: 24
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}




    renderChart2() {
        if (this.chart2) {
            this.chart2.destroy();
        }

        const data = this.state.get_sales_by_channel_last_5_months_data;

        if (!data || !data.labels || !Array.isArray(data.datasets)) {
            console.warn("Formato inválido de 'sales_distribution_by_channel'");
            return;
        }

        this.chart2 = new Chart(this.canvasRef2.el, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: data.datasets.map((ds, index) => ({
                    label: ds.label || `Dataset ${index + 1}`,
                    data: ds.data || [],
                    backgroundColor: index === 0 ? 'rgba(75, 192, 192, 0.2)' : 'rgba(144, 238, 144, 0.5)',
                    borderColor: index === 0 ? 'rgb(75, 192, 192)' : 'rgb(144, 238, 144)',
                    tension: 0.1
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Sales Distribution by Channel',
                        font: {
                            size: 24
                        }
                    }
                },
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }


    renderChart3() {
        if (this.chart3) {
            this.chart3.destroy();
        }
    
        // Datos del dataset
        let dataset = this.state.top_5_categories_data;
        console.log("Top Categories Data:", dataset);
        if (!Array.isArray(dataset)) {
            console.log(dataset);
            console.warn("El valor de 'datos' no es un array. Asignando un array vacío.");
            dataset = []; // Asegurar que 'datos' sea siempre un array
        }
    
        // Extraer etiquetas y datos
        const labels = dataset.map(item => item.category);
        const data = dataset.map(item => item.sales);
    
        // Configuración del gráfico
        this.chart3 = new Chart(this.canvasRef3.el, {
            type: "doughnut",  // Cambiado a 'doughnut' para gráfico de dona
            data: {
                labels: labels, // Usar categorías del dataset como etiquetas
                datasets: [
                    {
                        label: 'Sales Distribution',
                        data: data,  // Usar datos de ventas del dataset
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(255, 159, 64, 0.6)',
                            'rgba(153, 102, 255, 0.6)',
                            'rgba(255, 205, 86, 0.6)',
                            'rgba(54, 162, 235, 0.6)'
                        ],
                        borderColor: [
                            'rgb(75, 192, 192)',
                            'rgb(255, 159, 64)',
                            'rgb(153, 102, 255)',
                            'rgb(255, 205, 86)',
                            'rgb(54, 162, 235)'
                        ],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top Categories Sold',  // Título actualizado
                        font: {
                            size: 24  // Tamaño del título
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(tooltipItem) {
                                let label = tooltipItem.label || '';
                                let value = tooltipItem.raw || 0;
                                return `${label}: $${value.toFixed(2)} in sales`;
                            }
                        }
                    }
                }
            }
        });
    }
    

renderChart4() {
    if (this.chart4) {
        this.chart4.destroy();
    }

    const data = this.state.monthly_profit_last_6_months;

    if (!data || !data.labels || !Array.isArray(data.datasets)) {
        console.warn("Formato inválido en 'monthly_profit_last_6_months'");
        return;
    }

    this.chart4 = new Chart(this.canvasRef4.el, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, index) => ({
                label: ds.label || `Serie ${index + 1}`,
                data: ds.data || [],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Total Earnings',
                    font: {
                        size: 24
                    }
                }
            },
            scales: {
                y: {
                    stacked: true,
                    grid: {
                        display: true,
                        color: "rgba(255,99,132,0.2)"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}


renderChart5() {
    if (this.chart5) {
        this.chart5.destroy();
    }

    const data = this.state.CompletedAndCanceled4months_data;

    if (!data || !data.labels || !Array.isArray(data.datasets)) {
        console.warn("Formato inválido en 'CompletedAndCanceled4months_data'");
        return;
    }

    this.chart5 = new Chart(this.canvasRef5.el, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, index) => ({
                label: ds.label || `Serie ${index + 1}`,
                data: ds.data || [],
                backgroundColor: index === 0 ? 'rgba(75, 92, 192, 0.4)' : 'rgba(120, 38, 144, 0.5)',
                borderColor: index === 0 ? 'rgba(75, 92, 192, 0.4)' : 'rgba(120, 38, 144, 0.5)',
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Completed And Canceled',
                    font: {
                        size: 24
                    }
                }
            },
            scales: {
                y: {
                    stacked: false,
                    grid: {
                        display: true,
                        color: "rgba(255,99,132,0.2)"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

    

    renderChart6() {
        if (this.chart6) {
            this.chart6.destroy();
        }

        this.chart6 = new Chart(this.canvasRef6.el, {
            type: "bar",
            data: {
                labels: ['Proteins', 'Vitamins', 'Amino Acids', 'Pre-Workouts', 'Post-Workouts', 'Fat Burners'],
                datasets: [
                    {
                    label: 'History',
                    data: [15, 35, 55, 75, 52, 33]                    ,
                    backgroundColor: 'rgba(248, 186, 215, 0.6)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },             
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top products', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart7() {
        if (this.chart7) {
            this.chart7.destroy();
        }
        this.chart7 = new Chart(this.canvasRef7.el, {

            type: "bar",
            data: {
                labels: ['January', 'February', 'March', 'April'],
                datasets: [
                    {
                    label: 'Total Sale - Commissions, shipping and Ads',
                    data: [20, 40, 60, 80]                    ,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },             
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top Clients', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }

        });
    }

renderChart8() {
    if (this.chart8) {
        this.chart8.destroy();
    }

    const data = this.state.question_count_by_category_data;

    if (!data || !data.labels || !Array.isArray(data.datasets)) {
        console.warn("Formato inválido en 'question_count_by_category_data'");
        return;
    }

    this.chart8 = new Chart(this.canvasRef8.el, {
        type: "bar",
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, index) => ({
                label: ds.label || `Serie ${index + 1}`,
                data: ds.data || [],
                backgroundColor: 'rgba(248, 186, 215, 0.6)',
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Questions',
                    font: {
                        size: 24
                    }
                }
            },
            scales: {
                y: {
                    stacked: true,
                    grid: {
                        display: true,
                        color: "rgba(255,99,132,0.2)"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}


renderChart9() {
    if (this.chart9) {
        this.chart9.destroy();
    }

    const data = this.state.average_custom_order;

    if (!data || !data.labels || !Array.isArray(data.datasets)) {
        console.warn("Formato inválido en 'average_custom_order'");
        return;
    }

    this.chart9 = new Chart(this.canvasRef9.el, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, index) => ({
                label: ds.label || `Serie ${index + 1}`,
                data: ds.data || [],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }))
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Average Customer Order',
                    font: {
                        size: 24
                    }
                }
            },
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}


    onWillUnmount() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (this.chart2) {
            this.chart2.destroy();
        }

        if (this.chart9) {
            this.chart9.destroy();
        }
    }

    async sendMassMessage() {
        if (!this.state.selectedSegment) {
            alert("Por favor, seleccione un segmento antes de enviar.");
            return;
        }

        const success = await this.orm.call(
            "res.partner.segment",
            "send_mass_message",
            // AQUÍ CAMBIAS AL MODELO DE SEGMENTOS DE ODOO ESTO ES SOLO PRUEBA
            [this.state.selectedSegment, this.state.title, this.state.description]
        );

        if (success) {
            alert("Mensaje enviado exitosamente.");
        } else {
            alert("Hubo un error al enviar el mensaje.");
        }

        this.toggleModal(false);
    }
}

registry.category("actions").add("odoo-mercadolibre.welcome", Welcome);


