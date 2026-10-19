odoo.define('website_address_city.portal', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var portal = require('portal.portal');

    function cities_data(state) {
        if (state) {
            ajax.jsonRpc('/shop/cities_infos', 'call', {
                'state': state, 'country': $('select[name="country_id"]').val()
            }).then(function (data) {
                
                var selectcity = $("select[name='city_id']");
                var customer_city = selectcity.val();
                
                if (data && !(data.cities == undefined) && !(data.cities.length == 0)) {
                    selectcity.html('');
                    _.each(data.cities, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0]).attr('zipcode',x[2]);
                        selectcity.append(opt);
                    });
                    $("input[name='city']").val('')
                    $("input[name='city']").parent('div').hide();
                    selectcity.parent('div').show();
                    var zipcode = selectcity.find(":selected").attr('zipcode');
                    if(customer_city){
                        selectcity.val(customer_city);
                        if (selectcity.find(":selected").attr('zipcode') != 'false'){
                        $("input[name='zipcode']").val(parseInt(selectcity.find(":selected").attr('zipcode')));
                        }
                    }
                    else{

                        
                    if ( zipcode!= 'false'){
                        
                        $("input[name='zipcode']").val(parseInt(zipcode));
                    }
                }
                    
                } else {
                    selectcity.val('').parent('div').hide();
                    $("input[name='city']").parent('div').show();
                }
            });
        }
        else {
            $("select[name='city_id']").html('').parent('div').hide();
            $("input[name='city']").parent('div').show();
            return;
        }

    }

    function changeCountry_city() {
        if ($('select[name="state_id"]').val()) {
            var state = $('select[name="state_id"]').val();
        }
        else {
            $("select[name='city_id']").html('').parent('div').hide();
            $("input[name='city']").parent('div').show();
            return;
        }
        cities_data(state);
    }

    publicWidget.registry.portalDetails.include({
        _adaptAddressForm: function () {
            var res = this._super.apply(this, arguments);
            var $country = this.$('select[name="country_id"]');
            var countryID = ($country.val() || 0);
            ajax.jsonRpc('/country/state/check', 'call', {
                'country': countryID
            }).then(function (data) {
                if (data.result) {
                    
                    changeCountry_city()
                }
                else {
                    
                    $("select[name='city_id']").html('').parent('div').hide();
                    $("input[name='city']").parent('div').show();
                }
            });
            return res;
        }
    });


    publicWidget.registry.statesCities = publicWidget.Widget.extend({
        selector: '.o_portal_details',
        events: {
            'change select[name="state_id"]': '_onChangeState_city',
            'change select[name="city_id"]': '_onChange_city',
        },
        _onChangeState_city: function (ev) {
            var state = $('select[name="state_id"]').val();
            cities_data(state);
        },
        _onChange_city: function(ev){
            var selectcity = $(ev.currentTarget);
            var zipcode = selectcity.find(":selected").attr('zipcode');
            if ( zipcode!= 'false'){
                $("input[name='zipcode']").val(parseInt(zipcode))
            }
        }
    });
});