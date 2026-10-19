# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_tmpl_pvp = fields.Monetary(
        'PVP', default=1,currency_field='currency_id', compute='_compute_product_pvp'
    )

    @api.depends('list_price')
    def _compute_product_pvp(self):
        for record in self:
            record.product_tmpl_pvp =  record.list_price*1.19

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)
        default_code = ''
        pvp = 0
        if combination_info.get('product_id'):
            product_id = self.env['product.product'].browse(combination_info['product_id'])
            default_code = product_id.default_code
            pvp = product_id.product_product_pvp
            if pvp == 1:
                pvp = product_id.product_tmpl_id.product_tmpl_pvp
        if not default_code and combination_info.get('product_template_id'):
            product_id = self.env['product.template'].browse(combination_info['product_template_id'])
            default_code = product_id.default_code
            pvp = product_id.product_tmpl_pvp
        combination_info['default_code'] = default_code
        combination_info['pvp'] = pvp
        return combination_info

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: