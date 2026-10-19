
from datetime import datetime

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    qty_to_print = fields.Integer(string="Qty to print", default=1)
    date_last_purchase = fields.Datetime(
        'Fecha ultima compra',
        compute="_compute_last_purchase")
    qty_last_purchase = fields.Float(
        'Cant. ultima compra',
        compute="_compute_last_purchase")
    price_last_purchase = fields.Float(
        'Precio ultima compra',
        compute="_compute_last_purchase")
    wholesale_price = fields.Many2one(
        'product.pricelist.item',
        'Precio al mayor',
        compute="_compute_last_purchase")
    wholesale_price_2 = fields.Many2one(
        'product.pricelist.item',
        'Precio al mayor 2',
        compute="_compute_last_purchase")
    spacial_price = fields.Char(
        'Precio especial',
        compute="_compute_last_purchase")

    def _get_date(self, date, year=False):
        if year:
            return str(date.year)[2:]
        return str(date.month).zfill(2)

    def _get_price(self, price):
        if not price:
            return '00'
        price_cast = str(price).split('.')
        if price_cast[-1] != '00':
            return price
        return int(price)

    def _compute_last_purchase(self):

        order_line = self.env['purchase.order.line']
        pricelist_item = self.env['product.pricelist.item']

        for rec in self:

            rec.date_last_purchase = False
            rec.qty_last_purchase = 0.0
            rec.price_last_purchase = 0.0
            rec.wholesale_price = False
            rec.wholesale_price_2 = False
            rec.spacial_price = False

            line_id = order_line.search(
                [('product_id', '=', rec.id),
                 ('order_id.state', 'in', ['done', 'purchase'])],
                limit=1, order='id desc')

            if line_id:
                rec.date_last_purchase = line_id.date_planned
                rec.qty_last_purchase = line_id.product_qty
                rec.price_last_purchase = line_id.price_unit

                for item in self.env['product.pricelist.item'].search([('product_tmpl_id', '=', rec.product_tmpl_id.id)]):
                    if item.min_quantity == 1:
                        rec.spacial_price = '{}{}00{}'.format(
                            self._get_date(rec.date_last_purchase),
                            self._get_price(item.fixed_price),
                            self._get_date(rec.date_last_purchase, year=True),
                        )

            item = pricelist_item.search(
                [('product_id', '=', rec.id),
                 ('min_quantity', '=', 3)], order='id desc', limit=1)

            if not item:
                item = pricelist_item.search(
                    [('product_tmpl_id', '=', rec.product_tmpl_id.id),
                     ('min_quantity', '=', 3)],
                    order='id desc', limit=1)

            rec.wholesale_price = item.id if item else False

            item2 = pricelist_item.search(
                [('product_id', '=', rec.id),
                 ('min_quantity', '>', 3)], order='min_quantity asc', limit=1)

            if not item2:
                item2 = pricelist_item.search(
                    [('product_tmpl_id', '=', rec.product_tmpl_id.id),
                     ('min_quantity', '>', 3)],
                    order='min_quantity asc', limit=1)

            rec.wholesale_price_2 = item2.id if item2 else False

    def action_print_barcode(self):
        pass
