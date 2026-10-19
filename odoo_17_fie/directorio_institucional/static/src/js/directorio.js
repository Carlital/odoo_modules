/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.DirectorioInstitucional = publicWidget.Widget.extend({
    selector: '.s_directorio_institucional',
    events: {
        'click #btn-filtrar-directorio': '_onFiltrar',
        'keyup #busqueda_nombre': '_onKeyup',
        'change #filtro_unidad': '_onFiltrar',
        'click .directorio-page': '_onPaginate',
    },

    start: function () {
        console.log('[Directorio] Widget iniciado');
        this.currentPage = 1;
        this.limit = 12;
        this._cargarUnidades();
        this._onFiltrar();
        return this._super.apply(this, arguments);
    },

    _onKeyup: function (ev) {
        if (ev.key === 'Enter') {
            this._onFiltrar();
        }
    },

    _onPaginate: function (ev) {
        ev.preventDefault();
        this.currentPage = parseInt($(ev.currentTarget).data('page'));
        this._onFiltrar();
        this._scrollToResults();
    },

    _onFiltrar: function (ev = null) {
        const self = this;
        const unidad = this.$('#filtro_unidad').val();
        const nombre = this.$('#busqueda_nombre').val();

        if (!ev || ev.type !== 'click' || !$(ev.currentTarget).hasClass('directorio-page')) {
            this.currentPage = 1;
        }

        console.log('[Directorio] Filtrando - Unidad:', unidad, 'Nombre:', nombre, 'Página:', this.currentPage);

        // Mostrar indicador de carga
        this.$('#lista-directorio').html(`
            <div class="col-12">
                <div class="directorio-loading">
                    <i class="fa fa-spinner fa-spin"></i>
                    <p class="mt-3">Cargando directorio...</p>
                </div>
            </div>
        `);

        jsonrpc('/directorio_institucional/filtrar', {
            unidad: unidad || null,
            nombre: nombre || null,
            page: this.currentPage,
            limit: this.limit
        }).then(function (result) {
            console.log('[Directorio] Resultado recibido:', result);
            self.$('#lista-directorio').html(result.html);
            self.$('#pagination-directorio').html(result.pagination);
        }).catch(function (err) {
            console.error('[Directorio] Error:', err);
            self.$('#lista-directorio').html(`
                <div class="col-12">
                    <div class="alert alert-danger">
                        <i class="fa fa-exclamation-triangle"></i>
                        Error al cargar el directorio. Por favor, intente nuevamente.
                    </div>
                </div>
            `);
        });
    },

    _cargarUnidades: function () {
        const self = this;
        console.log('[Directorio] Cargando unidades...');
        
        jsonrpc('/directorio_institucional/unidades', {}).then(function (result) {
            console.log('[Directorio] Unidades recibidas:', result);
            if (result.unidades && result.unidades.length > 0) {
                result.unidades.forEach(function (unidad) {
                    self.$('#filtro_unidad').append(
                        $('<option></option>').attr('value', unidad.id).text(unidad.name)
                    );
                });
            }
        }).catch(function (err) {
            console.error('[Directorio] Error al cargar unidades:', err);
        });
    },

    _scrollToResults: function () {
        const resultsSection = this.$el[0];
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
});
