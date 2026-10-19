
from odoo import api, fields, models
from pytz import timezone, UTC


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ref_supplier_code = fields.Char(
        'Número', required=True, copy=False)
    ref_supplier_serie = fields.Char(
        'Serie', required=True, copy=False)
    purchase_in_dollar = fields.Boolean('USD')
    purchase_rate = fields.Float(
        digits=(12, 6), default=1.0, string='Tasa',
        tracking=True)

    _sql_constraints = [
        ('code_partner_ref_uniq',
            'unique (partner_ref, partner_id)',
            'El número y la serie deben ser unicos por proveedor !')]

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if self.purchase_in_dollar:
            self._create_or_update_rate(self.purchase_rate)
        return res

    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        for order in self:
            min_date = fields.Datetime.now()
            for line in order.order_line:
                if not min_date or line.date_planned < min_date:
                    min_date = line.date_planned
            if min_date:
                order.date_planned = min_date

    @api.onchange('purchase_rate')
    def onchange_purchase_rate(self):
        pass

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for r in self:
            r.purchase_in_dollar = False
            if r.currency_id and r.currency_id.name == 'USD':
                rate_obj = self.env['res.currency.rate']
                r.purchase_in_dollar = True
                l10n_currency_id = r.company_id.currency_id or self.env.company.currency_id
                date_ref = r.date_approve or r.date_order or fields.Datetime.now()
                rate_ids = rate_obj.search([
                    ('currency_id', '=', l10n_currency_id.id),
                    ('name', '<=', date_ref),
                    ('company_id', '=', r.company_id.id or self.env.company.id)],
                    order="name desc")
                rate = 1.0
                if rate_ids:
                    rate = rate_ids[0].rate
                r.purchase_rate = rate

    @api.onchange('ref_supplier_code', 'ref_supplier_serie')
    def _onchange_refpartner(self):
        for r in self:
            r.partner_ref = ''
            if r.ref_supplier_code and r.ref_supplier_serie:
                r.partner_ref = r.ref_supplier_serie + '-' + r.ref_supplier_code

    def _create_or_update_rate(self, rate, res=None):
        if not res:
            res = self
        rate_obj = self.env['res.currency.rate']
        company = res.company_id or self.env.company
        utc_date = res.date_approve or fields.Datetime.now()
        # Usar la zona horaria del usuario o UTC por defecto, evitar hardcode
        tz_name = self.env.user.tz or 'UTC'
        local_tz = timezone(tz_name)
        local_date = utc_date.replace(tzinfo=UTC).astimezone(local_tz)
        rate_ids = rate_obj.search([
            ('currency_id', '=', res.currency_id.id),
            ('name', '=', local_date),
            ('company_id', '=', company.id)],
            order="name desc")
        if not rate_ids:
            rate_obj.create({
                'currency_id': res.currency_id.id,
                'inverse_company_rate': rate,
                'name': local_date,
                'company_id': company.id,
            })

    """
    def print_report_price(self):
        return self.env['product.template'].print_report_label_price(
            self.id, True)

    def print_report_barcode(self):
        return self.env['product.template'].print_report_label_price(
            self.id)
    """


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    acs_pricelist_upd = fields.Boolean(
        'Lista de precios actualizada')

    price_unit_pen = fields.Float(
        'Precio unitario (Soles)',
        digits='Product Price',
        compute="_compute_price_unit_pen")

    price_unit_with_discount = fields.Float(
        'Precio unitario (Descuento)',
        digits='Product Price',
        compute="_compute_price_unit_with_discount", store=True)

    @api.depends('price_unit', 'discount')
    def _compute_price_unit_with_discount(self):
        for rec in self:
            rec.price_unit_with_discount = rec.price_unit
            if rec.discount:
                rec.price_unit_with_discount = rec.price_unit - (
                    rec.price_unit * rec.discount / 100)

    def _compute_price_unit_pen(self):
        rate_obj = self.env['res.currency.rate']
        for rec in self:
            rate = 1.0
            if rec.currency_id.name == 'USD':
                l10n_currency_id = rec.company_id.currency_id or self.env.company.currency_id
                rate_ids = rate_obj.search([
                    ('currency_id', '=', l10n_currency_id.id),
                    ('name', '<=', rec.order_id.date_order or fields.Datetime.now()),
                    ('company_id', '=', rec.company_id.id or self.env.company.id)],
                    order="name desc")
                if rate_ids:
                    rate = rate_ids[0].rate
            rec.price_unit_pen = rec.price_unit * rate

    def call_wizard_pricelist(self):
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
