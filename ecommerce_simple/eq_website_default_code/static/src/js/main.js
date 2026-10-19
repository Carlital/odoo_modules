odoo.define('eq_website_default_code.VariantMixin', function(require) {
'use strict';

const {Markup} = require('web.utils');
var VariantMixin = require('sale.VariantMixin');
var publicWidget = require('web.public.widget');

require('website_sale.website_sale');

VariantMixin._onChangeProductDefaultcode = function(ev, $parent, combination) {
	var $default_code = $parent.find('.default_code');
	var $pvp = $parent.find('.pvp');

	$default_code.text(combination.default_code || '');
	var formattedPvp = new Intl.NumberFormat('de-DE').format(combination.pvp);
	$pvp.text(formattedPvp || '');
};

publicWidget.registry.WebsiteSale.include({

	_onChangeCombination : function() {
		this._super.apply(this, arguments);
		VariantMixin._onChangeProductDefaultcode.apply(this, arguments);
	}
});

return VariantMixin;

});