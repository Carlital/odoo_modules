from odoo import models, fields, api


class ProductPriceVisibilityMixin(models.AbstractModel):
    """
    Mixin model to add a computed field that checks if the current user
    should see product prices.
    """
    _name = 'acs.product.price.visibility.mixin'
    _description = 'Product Price Visibility Mixin'

    acs_show_prices = fields.Boolean(
        string='Show Prices',
        compute='_compute_acs_show_prices',
        help="Technical field to control price visibility based on user settings."
    )

    @api.depends_context('uid')
    def _compute_acs_show_prices(self):
        """
        Compute if prices should be shown based on current user settings.
        The price is shown if the user does NOT have the 'acs_hide_prices' flag set.
        """
        # The value is the same for all records in the set, so compute it once.
        show_prices = not self.env.user.acs_hide_prices
        for record in self:
            record.acs_show_prices = show_prices


class ProductTemplate(models.Model, ProductPriceVisibilityMixin):
    _inherit = 'product.template'


class ProductProduct(models.Model, ProductPriceVisibilityMixin):
    _inherit = 'product.product'
