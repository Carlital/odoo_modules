# -*- coding: utf-8 -*-

from odoo import fields, models, tools


class CommissionSummary(models.Model):
    _name = 'commission.summary'
    _description = 'Resumen de Comisiones'
    _auto = False
    _order = 'date_order desc, sale_order_name'

    # Campos de la vista
    date_order = fields.Datetime(string='Fecha', readonly=True)
    sale_order_name = fields.Char(string='Nº de Pedido', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', readonly=True)
    seller_id = fields.Many2one('res.users', string='Vendedor', readonly=True)
    amount_untaxed = fields.Monetary(
        string='Monto Sin IGV (Moneda Original)', readonly=True, currency_field='currency_id')
    acs_type_exchange = fields.Float(
        string='Tipo de cambio', readonly=True, digits=(16, 4))
    acs_amount_pen = fields.Monetary(
        string='Monto en soles', readonly=True, currency_field='company_currency_id')
    sale_part_pen = fields.Monetary(
        string='Parte de Venta (Soles)', readonly=True, currency_field='company_currency_id')
    sale_part_original_currency = fields.Monetary(
        string='Parte de Venta (Moneda Original)', readonly=True, currency_field='currency_id')
    commission_amount = fields.Monetary(
        string='Comisión', readonly=True, currency_field='company_currency_id')

    # Campo calculado para el porcentaje
    commission_percentage = fields.Float(
        string='% Parte de venta', readonly=True, digits=(16, 2))

    # Campo auxiliar para identificar el sale_order original
    sale_order_id = fields.Many2one(
        'sale.order', string='Orden de Venta', readonly=True)

    # Campos de moneda para mostrar símbolos correctos
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', readonly=True)
    company_currency_id = fields.Many2one(
        'res.currency', string='Moneda Compañía', readonly=True)

    def init(self):
        """
        Crea la vista SQL que sirve como fuente de datos para este modelo. La vista une los datos de
        comisiones para el vendedor 1 y el vendedor 2 de cada orden de venta confirmada, facturada y
        totalmente pagada.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                WITH base_sales AS (
                    SELECT
                        so.id, so.date_order, so.name, so.partner_id, so.user_id,
                        so.x_seller2_id, so.amount_untaxed, so.currency_id,
                        so.acs_type_exchange,
                        (so.amount_untaxed * so.acs_type_exchange) AS acs_amount_pen,
                        so.x_commission_part_seller1, so.x_commission_part_seller2,
                        so.x_sale_part_seller1, so.x_sale_part_seller2,
                        so.x_sale_part_pen_seller1, so.x_sale_part_pen_seller2,
                        comp.currency_id as company_currency_id,
                        comp.acs_commission
                    FROM sale_order so
                    LEFT JOIN res_company comp ON (so.company_id = comp.id)
                    WHERE so.state = 'sale'
                        AND so.invoice_status = 'invoiced'
                        AND (
                            SELECT bool_and(am.payment_state = 'paid')
                            FROM account_move am
                            WHERE am.invoice_origin = so.name
                            AND am.company_id = so.company_id
                            AND am.move_type = 'out_invoice'
                            AND am.state = 'posted'
                        ) IS TRUE
                )
                -- Registros para el Vendedor 1 (principal)
                SELECT
                    (bs.id * 10) + 1 AS id,
                    bs.id AS sale_order_id,
                    bs.date_order,
                    bs.name AS sale_order_name,
                    bs.partner_id,
                    bs.user_id AS seller_id,
                    bs.amount_untaxed,
                    bs.currency_id,
                    bs.company_currency_id,
                    bs.acs_type_exchange,
                    bs.acs_amount_pen,
                    bs.x_sale_part_pen_seller1 AS sale_part_pen,
                    bs.x_sale_part_seller1 AS sale_part_original_currency,
                    -- Usar el porcentaje original (ej: 1.0) y multiplicarlo por 100 para mostrarlo
                    bs.x_commission_part_seller1 * 100 AS commission_percentage,
                    (bs.x_sale_part_pen_seller1 * bs.acs_commission) AS commission_amount
                FROM base_sales bs
                WHERE bs.user_id IS NOT NULL AND bs.x_sale_part_pen_seller1 > 0

                UNION ALL

                -- Registros para el Vendedor 2 (si existe)
                SELECT
                    (bs.id * 10) + 2 AS id,
                    bs.id AS sale_order_id,
                    bs.date_order,
                    bs.name AS sale_order_name,
                    bs.partner_id,
                    bs.x_seller2_id AS seller_id,
                    bs.amount_untaxed,
                    bs.currency_id,
                    bs.company_currency_id,
                    bs.acs_type_exchange,
                    bs.acs_amount_pen,
                    bs.x_sale_part_pen_seller2 AS sale_part_pen,
                    bs.x_sale_part_seller2 AS sale_part_original_currency,
                    -- Usar el porcentaje original (ej: 0.0) y multiplicarlo por 100 para mostrarlo
                    bs.x_commission_part_seller2 * 100 AS commission_percentage,
                    (bs.x_sale_part_pen_seller2 * bs.acs_commission) AS commission_amount
                FROM base_sales bs
                WHERE bs.x_seller2_id IS NOT NULL AND bs.x_sale_part_pen_seller2 > 0
            )
        """ % self._table
        self.env.cr.execute(query)
