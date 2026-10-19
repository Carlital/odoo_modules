# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quotation_state = fields.Selection([
        ('cot_pendiente', 'Cot. Pendiente'),
        ('seguimiento', 'Seguimiento'),
        ('no_compra', 'No Compra'),
        ('aceptado', 'Aceptado'),
        ('no_contesta', 'No Contesta'),
        ('otra_cot', 'Otra Cotización'),
        ('aceptado_falta_pago', 'Aceptado/Falta Pago'),
    ], string='Estado de Cotización', default='cot_pendiente', help='Seleccione el estado de la cotización.')

    # Campo para registrar el motivo de la pérdida directamente en la orden
    lost_reason_id = fields.Many2one(
        'crm.lost.reason',
        string='Motivo de no compra',
        index=True,
        tracking=True)

    x_commission_part_seller1 = fields.Float(
        string='% Parte de comisión (Vendedor 1)',
        default=1.0,
        digits='Percentage',
        help="Porcentaje de la comisión asignada al Vendedor 1 (el vendedor principal de la orden)."
    )

    x_sale_part_seller1 = fields.Float(
        string='Parte de venta (Vendedor 1)',
        compute='_compute_sale_parts',
        digits='Monetary',
        store=True,
        help="Parte de la venta asignada al Vendedor 1 (el vendedor principal de la orden)."
    )

    # Campo para el segundo vendedor, que participa en la comisión
    x_seller2_id = fields.Many2one(
        'res.users',
        string='Vendedor 2',
        domain=[('x_is_commission_agent', '=', True)],
        help="Segundo vendedor que participa en la comisión de esta orden. Solo se mostrarán vendedores comisionistas."
    )

    x_sale_part_seller2 = fields.Float(
        string='Parte de venta (Vendedor 2)',
        compute='_compute_sale_parts',
        digits='Monetary',
        store=True,
        help="Parte de la venta asignada al Vendedor 2."
    )

    x_commission_part_seller2 = fields.Float(
        string='% Parte de comisión (Vendedor 2)',
        default=0.0,
        digits='Percentage',
        help="Porcentaje de la comisión asignada al Vendedor 2."
    )

    # Campo auxiliar para la moneda de la compañía
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True,
        store=True  # Importante: almacenar para que funcione con campos Monetary
    )

    # Campos monetarios para mostrar en soles peruanos
    x_sale_part_pen_seller1 = fields.Monetary(
        string='Parte de venta en Soles (Vendedor 1)',
        compute='_compute_sale_parts_pen',
        store=True,
        currency_field='company_currency_id',  # Referencia al campo auxiliar
        help="Parte de la venta en moneda de la compañía asignada al Vendedor 1."
    )

    x_sale_part_pen_seller2 = fields.Monetary(
        string='Parte de venta en Soles (Vendedor 2)',
        compute='_compute_sale_parts_pen',
        store=True,
        currency_field='company_currency_id',  # Referencia al campo auxiliar
        help="Parte de la venta en moneda de la compañía asignada al Vendedor 2."
    )

    @api.depends('amount_untaxed', 'x_commission_part_seller1', 'x_commission_part_seller2')
    def _compute_sale_parts(self):
        """Calcula la parte de la venta para cada vendedor basado en su porcentaje."""
        for order in self:
            order.x_sale_part_seller1 = order.amount_untaxed * order.x_commission_part_seller1
            order.x_sale_part_seller2 = order.amount_untaxed * order.x_commission_part_seller2

    @api.depends('amount_untaxed', 'x_commission_part_seller1', 'x_commission_part_seller2', 'acs_type_exchange')
    def _compute_sale_parts_pen(self):
        """Calcula la parte de la venta para cada vendedor basado en su porcentaje pero en soles."""
        for order in self:
            order.x_sale_part_pen_seller1 = order.amount_untaxed * \
                order.x_commission_part_seller1 * order.acs_type_exchange
            order.x_sale_part_pen_seller2 = order.amount_untaxed * \
                order.x_commission_part_seller2 * order.acs_type_exchange

    @api.constrains('x_commission_part_seller1', 'x_commission_part_seller2')
    def _check_commission_percentages(self):
        """Valida que la suma de los porcentajes de comisión sea 100%."""
        for order in self:
            total_percentage = order.x_commission_part_seller1 + order.x_commission_part_seller2
            if not float_is_zero(total_percentage - 1.0, precision_digits=2):
                raise ValidationError(
                    _("Revisar valores % de partes de comisiones, deben sumar 100%."))

    @api.constrains('user_id', 'x_commission_part_seller1', 'x_seller2_id', 'x_commission_part_seller2')
    def _check_seller_for_commission_part(self):
        """Valida que se asigne un vendedor si su parte de comisión es mayor a cero."""
        for order in self:
            if order.x_commission_part_seller1 > 0 and not order.user_id:
                raise ValidationError(
                    _("El Vendedor 1 es obligatorio si su parte de comisión es mayor a 0%."))
            if order.x_commission_part_seller2 > 0 and not order.x_seller2_id:
                raise ValidationError(
                    _("El Vendedor 2 es obligatorio si su parte de comisión es mayor a 0%."))
