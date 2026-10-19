
from odoo import api, fields, models
import ast


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_main = fields.Boolean('Es tarifa principal')
    is_cajon = fields.Boolean('Es tarifa de Cajón')


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    nickname = fields.Char('Nickname')

    @api.onchange('min_quantity')
    def _onchange_min_quantity_nickname(self):
        if not self.nickname:
            if self.min_quantity == 3:
                self.nickname = 'MAYORISTA'
            elif self.min_quantity > 3:
                self.nickname = 'IMPORTACION'


class PricePurchaseWizard(models.TransientModel):
    _name = "list.price.purchase.wizard"
    _description = "List Price Purchase Report"

    line_id = fields.Integer('Linea')
    data_ids = fields.Char('IDS')
    msg = fields.Char(' ', readonly=True)
    variation_price = fields.Float(' ')
    variation_price_integer = fields.Integer(' ')
    product_id = fields.Many2one(
        'product.product', 'Producto', readonly=True)
    product_standard_name = fields.Char(
        'Referencia interna',
        related="product_id.default_code"
    )
    standard_price = fields.Float(
        'Costo antiguo', readonly=True)
    order_price = fields.Float('Costo nuevo', readonly=True)
    line_ids = fields.One2many(
        'list.price.purchase.wizard.line',
        'template_id', string='Lines')
    show_previus = fields.Boolean('Previus')
    show_next = fields.Boolean('Next')
    this_update = fields.Boolean('This Update')
    currency_id = fields.Many2one('Moneda')

    partner_id = fields.Many2one('res.partner', 'Proveedor')

    profit_percentage_pu = fields.Char(
        related='partner_id.profit_percentage_pu', string='% Ganancia PU')
    profit_percentage_pm = fields.Char(
        related='partner_id.profit_percentage_pm', string='% Ganancia PM')
    profit_percentage_pc = fields.Char(
        related='partner_id.profit_percentage_pc', string='% Ganancia PC')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_id = self._context.get('line_id', False)
        ol = self.env['purchase.order.line'].browse(active_id)
        currency_id = ol.order_id.currency_id
        ids = sorted([x.id for x in ol.order_id.order_line])
        this_update = ol.acs_pricelist_upd
        standard_price = ol.product_id.product_tmpl_id.penultimate_purchase_price
        if ol.acs_pricelist_upd:
            standard_price = ol.product_id.product_tmpl_id.last_purchase_price
        if not standard_price:
            standard_price = ol.product_id.product_tmpl_id.standard_price

        # price_unit = ol.price_unit
        price_unit = ol.price_unit_with_discount

        if currency_id.name != 'PEN':
            price_unit = price_unit * ol.order_id.purchase_rate
        tax = ol.taxes_id[:1]
        if tax:
            tax = tax[0]
            if not tax.price_include:
                price_unit = (
                    price_unit * tax.amount / 100) + \
                    price_unit
        show_previus = True
        show_next = True
        if ol.id == ids[0]:
            show_previus = False
        if ol.id == ids[-1]:
            show_next = False
        count = 1
        for i in ids:
            if i == ol.id:
                break
            count += 1
        line_ids = [
            (0, 0, {
                'pricelist_item_id': False,
                'min_quantity': 1,
                'name': 'Precio Minorista',
                'price': ol.product_id.product_tmpl_id.list_price,
                'margin': ol.product_id.product_tmpl_id.list_price * 100 / standard_price - 100 if standard_price else 0.0,
                'price2': ((price_unit * (ol.product_id.product_tmpl_id.list_price * 100 / standard_price - 100)) / 100) + price_unit if standard_price else 0.0,
                'margin2': ol.product_id.product_tmpl_id.list_price * 100 / standard_price - 100 if standard_price else 0.0,
                'nickname': 'MINORISTA',
            })]
        items = self.env['product.pricelist.item'].search([
            '|',
            ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
            ('product_id', '=', ol.product_id.id)],
            order='min_quantity asc')
        for item in items:
            nickname = item.nickname
            if not nickname:
                if item.min_quantity == 3:
                    nickname = 'MAYORISTA'
                elif item.min_quantity > 3:
                    nickname = 'IMPORTACION'
            line_ids.append((0, 0, {
                'pricelist_item_id': item.id,
                'min_quantity': item.min_quantity,
                'price': item.fixed_price,
                'margin': item.fixed_price * 100 / standard_price - 100 if standard_price else 0.0,
                'price2': ((price_unit * (item.fixed_price * 100 / standard_price - 100)) / 100) + price_unit if standard_price else 0.0,
                'margin2': (item.fixed_price * 100 / standard_price - 100) if standard_price else 0.0,
                'name': item.pricelist_id.name,
                'is_cajon': item.pricelist_id.is_cajon,
                'nickname': nickname}))
        variation_price_integer = 0
        variation_price = price_unit - standard_price
        if variation_price == 0.0:
            variation_price_integer = 1
        elif variation_price > 0.0:
            variation_price_integer = 2
        res.update(
            {
                'partner_id': ol.order_id.partner_id.id or False,
                'line_ids': line_ids,
                'product_id': ol.product_id.id,
                'order_price': price_unit,
                'standard_price': standard_price,
                'line_id': ol.id,
                'data_ids': ids,
                'show_previus': show_previus,
                'show_next': show_next,
                'msg': str(count) + '/' + str(len(ids)),
                'variation_price': variation_price,
                'variation_price_integer': variation_price_integer,
                'this_update': this_update})
        return res

    def call_previus(self):
        data_ids = ast.literal_eval(self.data_ids)
        for index, val in enumerate(data_ids):
            if val == self.line_id:
                self = self.with_context(line_id=data_ids[index - 1])
                wizard_form = self.env.ref(
                    'acs_purchase.list_price_purchase_wizard_form', False)
                view_id = self.env['list.price.purchase.wizard']
                vals = {}
                new = view_id.create(vals)
                return {
                    'name': 'Actualización de precios',
                    'type': 'ir.actions.act_window',
                    'res_model': 'list.price.purchase.wizard',
                    'res_id': new.id,
                    'view_id': wizard_form.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new'
                }

    def call_next(self):
        data_ids = ast.literal_eval(self.data_ids)
        for index, val in enumerate(data_ids):
            if val == self.line_id:
                self = self.with_context(line_id=data_ids[index + 1])
                wizard_form = self.env.ref(
                    'acs_purchase.list_price_purchase_wizard_form', False)
                view_id = self.env['list.price.purchase.wizard']
                vals = {}
                new = view_id.create(vals)
                return {
                    'name': 'Actualización de precios',
                    'type': 'ir.actions.act_window',
                    'res_model': 'list.price.purchase.wizard',
                    'res_id': new.id,
                    'view_id': wizard_form.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new'
                }

    def update_wizard(self):

        sync_price = None
        if self.product_id.product_tmpl_id.equal_wholesale_import_price:
            for rec in self.line_ids:
                if rec.pricelist_item_id and \
                        rec.pricelist_item_id.pricelist_id.is_main and \
                        rec.pricelist_item_id.min_quantity == 3:
                    sync_price = rec.price2
                    break

        for rec in self.line_ids:
            if rec.pricelist_item_id:
                if sync_price is not None and \
                        rec.pricelist_item_id.pricelist_id.is_main and \
                        rec.pricelist_item_id.min_quantity == 1000:
                    rec.pricelist_item_id.fixed_price = sync_price
                else:
                    rec.pricelist_item_id.fixed_price = rec.price2

                rec.pricelist_item_id.nickname = rec.nickname
                if rec.is_cajon:
                    rec.pricelist_item_id.min_quantity = rec.min_quantity
            else:
                self.product_id.list_price = rec.price2

        active_id = self.line_id
        ol = self.env['purchase.order.line'].browse(active_id)

        ol.acs_pricelist_upd = True

        if self.show_next:

            data_ids = ast.literal_eval(self.data_ids)
            for index, val in enumerate(data_ids):
                if val == self.line_id:
                    self = self.with_context(line_id=data_ids[index + 1])
                    wizard_form = self.env.ref(
                        'acs_purchase.list_price_purchase_wizard_form', False)
                    view_id = self.env['list.price.purchase.wizard']
                    vals = {}
                    new = view_id.create(vals)
                    return {
                        'name': 'Actualización de precios',
                        'type': 'ir.actions.act_window',
                        'res_model': 'list.price.purchase.wizard',
                        'res_id': new.id,
                        'view_id': wizard_form.id,
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new'
                    }

        else:
            return {'type': 'ir.actions.act_window_close'}


class wizard_select_template_line(models.TransientModel):
    _name = "list.price.purchase.wizard.line"
    _description = 'Template Lines'

    template_id = fields.Many2one('list.price.purchase.wizard', 'Template')
    pricelist_item_id = fields.Many2one(
        'product.pricelist.item', 'Tarifa Item')
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Tarifa',
        related='pricelist_item_id.pricelist_id')
    min_quantity = fields.Float('Cantidad min.')
    factor = fields.Float('Factor')
    margin = fields.Float('Margen %')
    price = fields.Float('Precio Lista')
    margin2 = fields.Float('Margen % ')
    price2 = fields.Float('Precio Lista')
    name = fields.Char('Descripción')
    is_cajon = fields.Boolean('Es Cajon')
    nickname = fields.Char('Nickname')

    @api.onchange('margin2', 'price2')
    def _onchange_margin2(self):
        context = self._context
        if context.get('price2', False):
            new_cost = self.template_id.order_price
            price = self.price2
            total = price * 100 / new_cost - 100
            self.margin2 = total

        elif context.get('margin2', False):
            new_cost = self.template_id.order_price
            margin = self.margin2
            self.price2 = (new_cost * margin / 100) + new_cost

        else:
            self.margin2 = 0.0
            self.price2 = 0.0
