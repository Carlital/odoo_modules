odoo.define('website_address_city.website_sale', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var Websitesale = require('website_sale.website_sale');
    var ajax = require('web.ajax');


    function changeCountry_city() {
        if ($('select[name="state_id"]').val()){
            var state = $('select[name="state_id"]').val();
        }
        if ($('select[name="state_id"]').css('display') == 'none' || state == undefined) {
           $("select[name='city_id']").parent('div').hide();
           $("input[name='city']").parent('div').show();
           return;
       }
       
       ajax.jsonRpc('/shop/cities_infos', 'call', {
           'state': state, 'country': $('select[name="country_id"]').val()
       }).then(function (data) {
           var selectcity = $("select[name='city_id']");
           var customer_city = selectcity.val();
           
           if (selectcity.data('init') === 0 || selectcity.find('option').length === 1) {
               if (data && !(data.cities == undefined) && !(data.cities.length == 0)) {
                       selectcity.html('');
                       _.each(data.cities, function (x) {
                           var opt = $('<option>').text(x[1])
                               .attr('value', x[0]).attr('zipcode',x[2]);;
                           selectcity.append(opt);
                       });
                       $("input[name='city']").parent('div.div_city').hide();
                       selectcity.parent('div').show();
                       var zipcode = selectcity.find(":selected").attr('zipcode');
                       if(customer_city){
                        selectcity.val(customer_city);
                        if (selectcity.find(":selected").attr('zipcode') != 'false'){
                        $("input[name='zip']").val(parseInt(selectcity.find(":selected").attr('zipcode')));
                        }
                    }
                    else{

                        
                    if ( zipcode!= 'false'){
                        
                        $("input[name='zip']").val(parseInt(zipcode));
                    }
                }
               } else {
                   
                   selectcity.val('').parent('div').hide();
                   $("input[name='city']").parent('div').show();
               }
               selectcity.data('init', 0);
           } else {
               selectcity.data('init', 0);
           }
       });
   }
    
    
    publicWidget.registry.WebsiteSale.include({
        _changeCountry: function () {
            var res = this._super.apply(this, arguments);
            var country_id = $('#country_id').val();
                ajax.jsonRpc('/country/state/check', 'call', {
                    'country': country_id
                }).then(function (data) {
                    if (data){
                        var state = data.result;
                        changeCountry_city();
                    } 
                });
            
            return res;
        }
    })

    publicWidget.registry.stateCities = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'change select[name="state_id"]': '_onChangeState_city',
            'change select[name="city_id"]': '_onChange_city',
        },
        _onChangeState_city: function (ev) {
            if (!this.$('.checkout_autoformat').length) {
                return;
            }
            changeCountry_city();
        },
        _onChange_city: function(ev){
            var selectcity = $(ev.currentTarget);
            var zipcode = selectcity.find(":selected").attr('zipcode');
            if ( zipcode!= 'false'){
                $("input[name='zip']").val(parseInt(zipcode))
            }
        }
        
    });
});    