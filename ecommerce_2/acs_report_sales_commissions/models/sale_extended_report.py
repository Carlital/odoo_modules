# -*- coding: utf-8 -*-

from odoo import fields, models, tools


class SaleExtendedReport(models.Model):
    _name = 'sale.extended.report'
    _description = 'Reporte de ventas extendido'
    _auto = False
    _order = 'date_order desc'

    # Columnas del reporte según lo solicitado
    name = fields.Char(string='Nº de Pedido', readonly=True)
    date_order = fields.Datetime(string='Fecha', readonly=True)
    advisors = fields.Text(string='Asesor(es)', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', readonly=True)
    vat = fields.Char(string='RUC/DNI', readonly=True)
    rubro_ids = fields.Text(string='Rubro', readonly=True)
    address = fields.Char(string='Dirección', readonly=True)
    source_id = fields.Many2one(
        'utm.source', string='Canal de Contacto', readonly=True)
    contact_name = fields.Char(string='Contacto', readonly=True)
    contact_function = fields.Char(string='Cargo', readonly=True)
    contact_mobile = fields.Char(string='Teléfono', readonly=True)
    contact_email = fields.Char(string='Correo', readonly=True)
    quoted_products = fields.Text(string='Productos cotizados', readonly=True)
    amount_untaxed = fields.Monetary(string='Monto - Sub Total', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', readonly=True)
    acs_type_exchange = fields.Float(
        string='Tipo de Cambio', readonly=True, digits=(16, 4))
    company_currency_id = fields.Many2one(
        'res.currency', string='Moneda Compañía', readonly=True)
    x_sale_part_seller1 = fields.Monetary(
        string='Parte Venta V1 (Moneda Orig.)', readonly=True, currency_field='currency_id')
    x_sale_part_pen_seller1 = fields.Monetary(
        string='Parte Venta V1 (Soles)', readonly=True, currency_field='company_currency_id')
    x_sale_part_seller2 = fields.Monetary(
        string='Parte Venta V2 (Moneda Orig.)', readonly=True, currency_field='currency_id')
    x_sale_part_pen_seller2 = fields.Monetary(
        string='Parte Venta V2 (Soles)', readonly=True, currency_field='company_currency_id')

    quotation_state = fields.Selection([
        ('cot_pendiente', 'Cot. Pendiente'),
        ('seguimiento', 'Seguimiento'),
        ('no_compra', 'No Compra'),
        ('aceptado', 'Aceptado'),
        ('no_contesta', 'No Contesta'),
        ('otra_cot', 'Otra Cotización'),
        ('aceptado_falta_pago', 'Aceptado/Falta Pago'),
    ], string='Estado de cotización', readonly=True)
    lost_reason = fields.Char(string='Motivo de no compra', readonly=True)

    # Campos para navegación y filtros
    sale_order_id = fields.Many2one(
        'sale.order', string='Orden de Venta', readonly=True)
    user_id = fields.Many2one('res.users', string='Vendedor 1', readonly=True)
    x_seller2_id = fields.Many2one(
        'res.users', string='Vendedor 2', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # NOTA: Para los campos traducibles (nombre de producto, estado, motivo de pérdida),
        # extraemos la traducción 'es_ES'. Si tu idioma principal es otro,
        # puedes necesitar cambiar 'es_ES' por tu código de idioma (ej. 'en_US').
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    so.id,
                    so.name,
                    so.id as sale_order_id,
                    so.date_order,
                    -- Concatena asesores con saltos de línea y un guion
                    concat_ws(CHR(10),
                        CASE WHEN up1.name IS NOT NULL THEN concat('- ', up1.name) ELSE NULL END,
                        CASE WHEN up2.name IS NOT NULL THEN concat('- ', up2.name) ELSE NULL END) as advisors,
                    so.partner_id,
                    rp.vat,
                    (SELECT string_agg(concat('- ', rpr.name), E'\n')
                        FROM res_partner_res_partner_rubro_rel rprpr
                        JOIN res_partner_rubro rpr ON rprpr.res_partner_rubro_id = rpr.id
                        WHERE rprpr.res_partner_id = so.partner_id) as rubro_ids,
                    concat_ws(', ', rp.street, rp.city, rcs.name) as address,
                    so.source_id,
                    contact.name as contact_name,
                    contact.function as contact_function,
                    contact.mobile as contact_mobile,
                    contact.email as contact_email,
                    (SELECT string_agg(
                        concat('- ', sol.product_uom_qty, ' ',
                            -- Fallback para UoM sin traducción al español
                            COALESCE(uom.name->>'es_ES', uom.name->>'en_US', uom.name::text),
                            ' ', sol.name),
                        E'\n'
                     )
                     FROM sale_order_line sol
                     JOIN uom_uom uom ON sol.product_uom = uom.id
                     WHERE sol.order_id = so.id AND sol.display_type IS NULL) as quoted_products,
                    so.amount_untaxed,
                    so.currency_id,
                    so.company_currency_id,
                    so.x_sale_part_seller1,
                    so.x_sale_part_pen_seller1,
                    so.x_sale_part_seller2,
                    so.x_sale_part_pen_seller2,
                    so.acs_type_exchange,
                    so.quotation_state,                    
                    -- Fallback robusto para obtener el nombre del motivo de pérdida, priorizando español
                    COALESCE(clr.name->>'es_PE', clr.name->>'es_ES', clr.name->>'es', clr.name->>'en_US', clr.name::text) as lost_reason,
                    so.user_id,
                    so.x_seller2_id
                FROM
                    sale_order so
                    LEFT JOIN res_partner rp ON so.partner_id = rp.id
                    LEFT JOIN res_country_state rcs ON rp.state_id = rcs.id
                    LEFT JOIN res_partner contact ON so.contact_person_id = contact.id
                    LEFT JOIN res_users u1 ON so.user_id = u1.id
                    LEFT JOIN res_partner up1 ON u1.partner_id = up1.id
                    LEFT JOIN res_users u2 ON so.x_seller2_id = u2.id
                    LEFT JOIN res_partner up2 ON u2.partner_id = up2.id
                    LEFT JOIN crm_lost_reason clr ON so.lost_reason_id = clr.id
            )
        """ % self._table
        self.env.cr.execute(query)
