odoo.define('acs_pos_partner_searchs.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var chrome = require('point_of_sale.chrome');
    var PopupWidget = require('point_of_sale.popups');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var _t = core._t;
    var ProductCategoriesWidget = screens.ProductCategoriesWidget.include({
        init: function (parent, options) {
            var self = this;
            this._super(parent, options);
            this.partner_id = {}
            this.search_partner_pos = function () {
                self.search_advance_partner();
            };
            this.save_partner_pos = function () {
                self.easy_save_advance_partner();
            };

        },
        renderElement: function () {

            var self = this;
            this._super();
            this.el.querySelector('.partner_query_search').addEventListener('input', this.search_partner_pos);
            this.el.querySelector('.partner_query_search').addEventListener('blur', function () {
                setTimeout(() => {
                    $('#partner-info').html('');
                }, 200);
            });
            this.el.querySelector('.partner_query_search').addEventListener('focus', function () {
                if ($('#partner_query_search').val() != '') {
                    $('partner_query_search').trigger('input');
                }
            });
            this.el.querySelector('#savePartner').addEventListener('click', this.save_partner_pos);
        },
        easy_save_advance_partner: function () {
            var order = this.pos.get_order();
            var self = this;
            var query = $('.partner_query_search').val();
            if (query.length > 0) {
                rpc.query({
                    model: 'res.partner',
                    method: 'get_by_doc_number',
                    args: [query],
                }).then(function (result) {
                    if (result) {
                        rpc.query({
                            model: 'res.partner',
                            method: 'create_from_ui',
                            args: [result],
                        })
                            .then(function (partner_id) {
                                self.saved_easy_client_details(partner_id);
                                $('#partner-info').html('');
                            });
                    }
                });
            }
        },
        saved_easy_client_details: function (partner_id) {
            var self = this;
            var order = this.pos.get_order();
            return this.pos.load_new_partners().then(function () {
                let pricelist = _.findWhere(self.pos.pricelists, { 'id': self.pos.db.get_partner_by_id(partner_id).property_product_pricelist[0] }) || self.pos.default_pricelist
                var new_client = self.pos.db.get_partner_by_id(partner_id);
                var other_old = new_client.other;
                var id_client = new_client.id;
                new_client.other = '';
                if (new_client.doc_number.length == 11) {
                    self.gui.show_popup('select-single-direction', {
                        'title': 'Seleccione la Dirección',
                        'value': '',
                        'new_partner': new_client,
                        'confirm': function (value,other) {
                            if (value != "") {
                                var list_of_fields_to_change = ['id', 'street', 'street2', 'address', 'city', 'state_id', 'country_id', 'district_id']
                                var last_address = {}
                                for (var i = 0; i < list_of_fields_to_change.length; i++) {
                                    last_address[list_of_fields_to_change[i]] = new_client[list_of_fields_to_change[i]]
                                }
                                var new_address = ""
                                var aux_index = -1
                                for (let index = 0; index < new_client.address_array.length; index++) {
                                    if (value == new_client.address_array[index].id) {
                                        new_address = new_client.address_array[index]
                                        aux_index = index
                                    }
                                }
                                for (let index = 0; index < list_of_fields_to_change.length; index++) {
                                    if (list_of_fields_to_change[index] in new_client) {
                                        if (list_of_fields_to_change[index] == 'id') {
                                            new_client['id_original'] = new_address[list_of_fields_to_change[index]]
                                        } else {
                                            new_client[list_of_fields_to_change[index]] = new_address[list_of_fields_to_change[index]]
                                        }
                                        //new_client[list_of_fields_to_change[index]] = new_address[list_of_fields_to_change[index]]
                                    }
                                }
                                for (let index = 0; index < list_of_fields_to_change.length; index++) {
                                    if (list_of_fields_to_change[index] in last_address) {
                                        if (list_of_fields_to_change[index] == 'id') {
                                            new_client.address_array[aux_index]['id_original'] = last_address[list_of_fields_to_change[index]]
                                        } else {
                                            new_client.address_array[aux_index][list_of_fields_to_change[index]] = last_address[list_of_fields_to_change[index]]
                                        }
                                        //new_client.address_array[aux_index][list_of_fields_to_change[index]] = last_address[list_of_fields_to_change[index]]
                                    }
                                }
                                order.set_pricelist(pricelist);
                                order.set_client(new_client);

                                $(".partner_query_search").val('');
                            } else {
                                order.set_pricelist(pricelist);
                                order.set_client(new_client);

                                $(".partner_query_search").val('');
                            }
                            if (other != other_old) {
                                var fields = {}
                                fields.id = id_client
                                fields.other = other
                                rpc.query({
                                    model: 'res.partner',
                                    method: 'create_from_ui',
                                    args: [fields],
                                })
                                    .then(function (partner_id) {
                                        self.pos.gui.screen_instances.clientlist.saved_client_details(partner_id);
                                    }, function (err, ev) {
                                        ev.preventDefault();
                                        var error_body = _t('Your Internet connection is probably down.');
                                        if (err.data) {
                                            var except = err.data;
                                            error_body = except.arguments && except.arguments[0] || except.message || error_body;
                                        }
                                        self.gui.show_popup('error', {
                                            'title': _t('Error: Could not Save Changes'),
                                            'body': error_body,
                                        });
                                        contents.on('click', '.button.save', function () { self.save_client_details(partner); });
                                    });
                            }
                        },
                        'cancel': function () {
                            order.set_pricelist(pricelist);
                            order.set_client(new_client);
                            $(".partner_query_search").val('');
                        }
                    });

                } else {
                    order.set_pricelist(pricelist);
                    order.set_client(new_client);
                    $(".partner_query_search").val('');
                }
            });
        },
        search_advance_partner: function () {
            var order = this.pos.get_order();
            var query = $('.partner_query_search').val();
            var self = this;
            rpc.query({
                model: 'res.partner',
                method: 'get_partners',
                args: [query],
            }).then(function (result) {
                var keys = Object.keys(result)
                if (keys.length > 0) {
                    this.partner_id = result;
                    var partners = `<ul id="partner_select_acs">`;
                    for (var i = 0; i < keys.length; i++) {
                        partners += `<li class="partner_select_acs_item" data-partner_id="${result[keys[i]].id}">${result[keys[i]].name}</li>`;
                    }
                    partners += `</ul>`;
                    $('#partner-info').html(partners);
                    $('.partner_select_acs_item').on('click', function () {
                        var self1 = this;
                        let pricelist = _.findWhere(self.pos.pricelists, { 'id': self.pos.db.get_partner_by_id(self1.dataset.partner_id).property_product_pricelist[0] }) || self.pos.default_pricelist;
                        var new_client = self.pos.db.get_partner_by_id(self1.dataset.partner_id)
                        var other_old = new_client.other;
                        var id_client = new_client.id
                        if (new_client.child_ids.length > 0) {
                            self.gui.show_popup('select-direction', {
                                'title': 'Seleccione la Dirección',
                                'value': '',
                                'new_partner': new_client,
                                'confirm': function (value,other) {
                                    if (value != "") {
                                        var list_of_fields_to_change = ['id', 'street', 'street2', 'address', 'city', 'state_id', 'country_id', 'district_id']
                                        var last_address = {}
                                        for (var i = 0; i < list_of_fields_to_change.length; i++) {
                                            last_address[list_of_fields_to_change[i]] = new_client[list_of_fields_to_change[i]]
                                        }
                                        var new_address = ""
                                        var aux_index = -1
                                        for (let index = 0; index < new_client.address_array.length; index++) {
                                            if (value == new_client.address_array[index].id) {
                                                new_address = new_client.address_array[index]
                                                aux_index = index
                                            }
                                        }
                                        for (let index = 0; index < list_of_fields_to_change.length; index++) {
                                            if (list_of_fields_to_change[index] in new_client) {
                                                if (list_of_fields_to_change[index] == 'id') {
                                                    new_client['id_original'] = new_address[list_of_fields_to_change[index]]
                                                } else {
                                                    new_client[list_of_fields_to_change[index]] = new_address[list_of_fields_to_change[index]]
                                                }
                                                //new_client[list_of_fields_to_change[index]] = new_address[list_of_fields_to_change[index]]
                                            }
                                        }
                                        for (let index = 0; index < list_of_fields_to_change.length; index++) {
                                            if (list_of_fields_to_change[index] in last_address) {
                                                if (list_of_fields_to_change[index] == 'id') {
                                                    new_client.address_array[aux_index]['id_original'] = last_address[list_of_fields_to_change[index]]
                                                } else {
                                                    new_client.address_array[aux_index][list_of_fields_to_change[index]] = last_address[list_of_fields_to_change[index]]
                                                }
                                                //new_client.address_array[aux_index][list_of_fields_to_change[index]] = last_address[list_of_fields_to_change[index]]
                                            }
                                        }
                                        order.set_pricelist(pricelist);
                                        order.set_client(new_client);

                                        $(".partner_query_search").val('');
                                    } else {
                                        order.set_pricelist(pricelist);
                                        order.set_client(new_client);

                                        $(".partner_query_search").val('');
                                    }

                                    if (other != other_old) {
                                        var fields = {}
                                        fields.id = id_client
                                        fields.other = other
                                        rpc.query({
                                            model: 'res.partner',
                                            method: 'create_from_ui',
                                            args: [fields],
                                        })
                                            .then(function (partner_id) {
                                                self.pos.gui.screen_instances.clientlist.saved_client_details(partner_id);
                                            }, function (err, ev) {
                                                ev.preventDefault();
                                                var error_body = _t('Your Internet connection is probably down.');
                                                if (err.data) {
                                                    var except = err.data;
                                                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                                                }
                                                self.gui.show_popup('error', {
                                                    'title': _t('Error: Could not Save Changes'),
                                                    'body': error_body,
                                                });
                                                contents.on('click', '.button.save', function () { self.save_client_details(partner); });
                                            });
                                    }
                                },
                                'cancel': function () {

                                }
                            });
                        } else if (!new_client.clientes_varios) {
                            self.gui.show_popup('select-single-direction', {
                                'title': 'Seleccione la Dirección',
                                'value': '',
                                'new_partner': new_client,
                                'confirm': function (value,other) {
                                    if (value != "") {
                                        var list_of_fields_to_change = ['id', 'street', 'street2', 'address', 'city', 'state_id', 'country_id', 'district_id']
                                        var last_address = {}
                                        for (var i = 0; i < list_of_fields_to_change.length; i++) {
                                            last_address[list_of_fields_to_change[i]] = new_client[list_of_fields_to_change[i]]
                                        }
                                        var new_address = ""
                                        var aux_index = -1
                                        for (let index = 0; index < new_client.address_array.length; index++) {
                                            if (value == new_client.address_array[index].id) {
                                                new_address = new_client.address_array[index]
                                                aux_index = index
                                            }
                                        }
                                        for (let index = 0; index < list_of_fields_to_change.length; index++) {
                                            if (list_of_fields_to_change[index] in new_client) {
                                                if (list_of_fields_to_change[index] == 'id') {
                                                    new_client['id_original'] = new_address[list_of_fields_to_change[index]]
                                                } else {
                                                    new_client[list_of_fields_to_change[index]] = new_address[list_of_fields_to_change[index]]
                                                }
                                                //new_client[list_of_fields_to_change[index]] = new_address[list_of_fields_to_change[index]]
                                            }
                                        }
                                        for (let index = 0; index < list_of_fields_to_change.length; index++) {
                                            if (list_of_fields_to_change[index] in last_address) {
                                                if (list_of_fields_to_change[index] == 'id') {
                                                    new_client.address_array[aux_index]['id_original'] = last_address[list_of_fields_to_change[index]]
                                                } else {
                                                    new_client.address_array[aux_index][list_of_fields_to_change[index]] = last_address[list_of_fields_to_change[index]]
                                                }
                                                //new_client.address_array[aux_index][list_of_fields_to_change[index]] = last_address[list_of_fields_to_change[index]]
                                            }
                                        }
                                        order.set_pricelist(pricelist);
                                        order.set_client(new_client);

                                        $(".partner_query_search").val('');
                                    } else {
                                        order.set_pricelist(pricelist);
                                        order.set_client(new_client);

                                        $(".partner_query_search").val('');
                                    }

                                    if (other != other_old) {
                                        var fields = {}
                                        fields.id = id_client
                                        fields.other = other
                                        rpc.query({
                                            model: 'res.partner',
                                            method: 'create_from_ui',
                                            args: [fields],
                                        })
                                            .then(function (partner_id) {
                                                self.pos.gui.screen_instances.clientlist.saved_client_details(partner_id);
                                            }, function (err, ev) {
                                                ev.preventDefault();
                                                var error_body = _t('Your Internet connection is probably down.');
                                                if (err.data) {
                                                    var except = err.data;
                                                    error_body = except.arguments && except.arguments[0] || except.message || error_body;
                                                }
                                                self.gui.show_popup('error', {
                                                    'title': _t('Error: Could not Save Changes'),
                                                    'body': error_body,
                                                });
                                                contents.on('click', '.button.save', function () { self.save_client_details(partner); });
                                            });
                                    }
                                },
                                'cancel': function () {

                                }
                            });

                        } else {
                            order.set_pricelist(pricelist);
                            order.set_client(new_client);

                            $(".partner_query_search").val('');
                        }
                    });
                } else {
                    var partners = `<div id="partner_select_acs">`;
                    partners += `<div>No se encuentra clientes, si desea añadir de clic en el icono</div></div>`;
                    $('#partner-info').html(partners);
                }
            });
        },
    });

});

