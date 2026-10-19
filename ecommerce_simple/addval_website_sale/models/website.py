import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _

from odoo.http import request
from odoo.osv import expression
from odoo.addons.http_routing.models.ir_http import url_for

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    website_analytic_id = fields.Many2one(
        'account.analytic.account',
        string = 'Cuenta analítica Website',
        store = True,
        readonly=False,
    )

    def sale_get_order(self, force_create=False, update_pricelist=False):
        sale_order_sudo = super(Website, self).sale_get_order(force_create=force_create, update_pricelist=update_pricelist)
        
        sale_order_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', sale_order_sudo.id)])
 
        for line in sale_order_lines:
            line.analytic_distribution = {self.website_analytic_id.id: 100}
        return sale_order_sudo