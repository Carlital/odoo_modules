from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    acs_cant_pzs = fields.Float(
        string='Cant. Pzas',
        digits='Product Unit of Measure',
        default=0.0
    )
    acs_udv = fields.Many2one(
        'uom.uom',
        string='Udv',
        help='Unidad de medida informativa, no afecta los cálculos'
    )
    acs_largue_pza = fields.Float(
        string='Largo x Pza - mts',
        digits='Product Unit of Measure',
        default=0.0
    )
    acs_price_pza = fields.Float(
        string='Prec. x Pza',
        compute='_compute_acs_price_pza',
        store=True,
        digits='Product Price'
    )
    acs_line_color = fields.Many2one(
        'sale.order.line.colors',
        string='Color'
    )
    state = fields.Selection(
        related='order_id.state',
        string='Order Status',
        readonly=True,
        copy=False,
        store=True,
    )
    acs_manufacturing_display_name = fields.Text(
        string='Producto / Descripción',
        compute='_compute_acs_manufacturing_display_name',
    )
    product_purchase_ok = fields.Boolean(
        related='product_id.product_tmpl_id.purchase_ok',
        string="Producto Comprable"
    )
    acs_lot_serial = fields.Many2one(
        'stock.lot',
        string='Nº de Bobina',
        help="Selecciona el lote o número de serie para productos comprados."
    )

    acs_lot_stock_qty = fields.Float(
        string='Stock fuente',
        compute='_compute_acs_lot_stock_qty',
        digits='Product Unit of Measure',
        help="Muestra el stock disponible del lote/serie seleccionado."
    )

    acs_comments = fields.Char(
        string='Comentarios',
    )

    acs_observations = fields.Char(
        string='Observaciones',
        compute='_compute_acs_observations',
        store=True
    )

    @api.onchange('acs_lot_serial')
    def _onchange_acs_lot_serial_comments(self):
        if self.acs_lot_serial:
            self.acs_comments = 'SIN COMENTARIOS'
        else:
            self.acs_comments = ''

    @api.depends('acs_lot_serial', 'acs_lot_serial.name', 'acs_comments')
    def _compute_acs_observations(self):
        for line in self:
            parts = filter(None, [line.acs_lot_serial.name, line.acs_comments])
            line.acs_observations = ' - '.join(parts)

    @api.depends('acs_lot_serial')
    def _compute_acs_lot_stock_qty(self):
        for line in self:
            if line.acs_lot_serial:
                line.acs_lot_stock_qty = line.acs_lot_serial.product_qty
            else:
                line.acs_lot_stock_qty = 0.0

    @api.depends('name')
    def _compute_acs_manufacturing_display_name(self):
        """Prepara el nombre para mostrar en la vista de fabricación."""
        for line in self:
            line.acs_manufacturing_display_name = line.name

    @api.depends('acs_largue_pza', 'price_unit')
    def _compute_acs_price_pza(self):
        for line in self:
            line.acs_price_pza = line.acs_largue_pza * line.price_unit

    @api.depends('acs_cant_pzs', 'acs_largue_pza')
    def _compute_product_uom_qty(self):
        for line in self:
            line.product_uom_qty = line.acs_cant_pzs * line.acs_largue_pza

    # Sobreescribir el campo original
    product_uom_qty = fields.Float(
        string='Cantidad',
        compute='_compute_product_uom_qty',
        store=True,
        readonly=False,
        precompute=True
    )

    @api.onchange('product_id')
    def _onchange_product_id_acs(self):
        """
        Realiza varias acciones cuando el producto cambia:
        1. Limpia el lote seleccionado.
        2. Hace la UdM de solo lectura.
        """
        self.acs_lot_serial = False
        if self.product_id:
            return {'readonly': {'product_uom': True}}

    def write(self, vals):
        """Override write to create tracking messages for line changes."""
        tracking_fields = ['acs_lot_serial', 'acs_comments']
        if not any(field in vals for field in tracking_fields):
            return super().write(vals)

        old_values = {}
        for line in self:
            old_values[line.id] = {
                'order_id': line.order_id,
                'product_name': line.product_id.name or f"Línea {line.id}",
                'acs_lot_serial': line.acs_lot_serial.name or 'No establecido',
                'acs_comments': line.acs_comments or 'No establecido',
            }

        result = super().write(vals)

        for line in self:
            if line.id not in old_values or not old_values[line.id]['order_id']:
                continue

            messages = []
            order = old_values[line.id]['order_id']

            if 'acs_lot_serial' in vals:
                old_value = old_values[line.id]['acs_lot_serial']
                new_value = line.acs_lot_serial.name or 'No establecido'
                if old_value != new_value:
                    field_string = self._fields['acs_lot_serial'].string
                    messages.append(
                        f"| {field_string}: {old_value} ➜ {new_value}")

            if 'acs_comments' in vals:
                old_value = old_values[line.id]['acs_comments']
                new_value = line.acs_comments or 'No establecido'
                if old_value != new_value:
                    field_string = self._fields['acs_comments'].string
                    messages.append(
                        f"| {field_string}: {old_value} ➜ {new_value}")

            if messages:
                product_name = old_values[line.id]['product_name']
                message_body = f"Cambios en línea de producto: {product_name}\n" + "\n".join(
                    messages)
                order.message_post(body=message_body)

        return result

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepara los valores para crear la línea de factura.
        Extiende el método original para incluir los campos personalizados.
        """
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'acs_cant_pzs': self.acs_cant_pzs,
            'acs_udv': self.acs_udv.id,
            'acs_largue_pza': self.acs_largue_pza,
            'acs_price_pza': self.acs_price_pza,
        })
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_name = fields.Char(
        string='Cliente',
        related='partner_id.name',
        store=True
    )

    sequence_order_production = fields.Char(
        string='Número de Orden de Fabricación',
        readonly=True,
        copy=False
    )
    acs_type_exchange = fields.Float(
        string='Tipo de Cambio',
        compute='_compute_acs_type_exchange',
        store=True,
        digits=(12, 4)
    )
    acs_amount_pen = fields.Monetary(
        string='Monto PEN',
        compute='_compute_acs_amount_pen',
        store=True,
        currency_field='pen_currency_id',
        group_operator='sum'  # Agregamos esto para asegurar la suma
    )
    pen_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda PEN',
        default=lambda self: self.env.ref(
            'base.PEN', raise_if_not_found=False),
        store=True  # Agregamos store=True
    )
    pay_flete = fields.Selection([
        ('paga_cobertec', 'Paga Cobertec'),
        ('paga_cliente', 'Paga Cliente'),
    ], string='Pago de Flete', help='Seleccionar quién paga el flete')

    # obteniendo el contacto del cliente
    contact_person_id = fields.Many2one(
        'res.partner',
        string='Persona de Contacto',
        domain="[('parent_id', '=', partner_id), ('is_company', '=', False), ('type', '=', 'contact')]",
        help="Selecciona la persona de contacto específica de esta empresa"
    )
    # obteniendo el direcciones de entrega del cliente
    contact_delivery_id = fields.Many2one(
        'res.partner',
        string='Direcciones de entrega',
        domain="[('parent_id', '=', partner_id), ('is_company', '=', False), ('type', '=', 'delivery')]",
        help="Selecciona la dirección de entrega específica de esta empresa"
    )
    # Añadir tracking al campo nativo
    commitment_date = fields.Datetime(
        tracking=True
    )

    manufacturing_order_count = fields.Integer(
        compute='_compute_manufacturing_order_count',
        string="Órdenes de Fabricación"
    )

    # API para limpiar tanto el contacto como la dirección de entrega cuando cambia el cliente
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Limpia el contacto y dirección de entrega cuando cambia el cliente"""
        res = super()._onchange_partner_id()

        # Limpia los campos personalizados cuando cambia el cliente
        self.contact_person_id = False
        self.contact_delivery_id = False

        return res

    manufacturing_order_line_ids = fields.One2many(
        'sale.order.line',
        'order_id',
        string="Líneas de Fabricación",
        domain=[
            ('display_type', '=', False),
            ('product_id.product_tmpl_id.acs_exclude_from_manufacturing', '=', False),
        ],
        help="Líneas de pedido filtradas para mostrar solo productos, excluyendo secciones y notas."
    )

    def _get_exchange_rate_for_date(self, date):
        """Método auxiliar para obtener la tasa de cambio para una fecha dada."""
        self.ensure_one()
        rate = 1.0
        # Usamos pen_currency_id para ser consistentes con los otros campos
        if self.currency_id and self.currency_id != self.pen_currency_id:
            currency_rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.currency_id.id),
                ('company_id', '=', self.company_id.id),
                ('name', '<=', date)
            ], order='name DESC', limit=1)

            if currency_rate and currency_rate.rate:
                # Calculamos el inverso del rate para la conversión a PEN
                rate = 1.0 / currency_rate.rate
        return rate

    @api.depends('date_order', 'currency_id', 'state')
    def _compute_acs_type_exchange(self):
        for order in self:
            if order.state in ('sale', 'done'):
                continue
            # El cálculo inicial usa la fecha del pedido
            order.acs_type_exchange = order._get_exchange_rate_for_date(
                order.date_order or fields.Date.today())

    @api.depends('amount_total', 'acs_type_exchange', 'state', 'pen_currency_id')
    def _compute_acs_amount_pen(self):
        for order in self:
            # Asegurar que pen_currency_id esté establecido
            if not order.pen_currency_id:
                order.pen_currency_id = self.env.ref(
                    'base.PEN', raise_if_not_found=False)

            # Si el pedido está confirmado y ya tiene un valor, no lo recalculamos.
            # Esto "congela" el valor después de la confirmación.
            if order.state in ('sale', 'done') and order.acs_amount_pen:
                continue
            order.acs_amount_pen = order.amount_total * order.acs_type_exchange

    def action_confirm(self):
        # Primero, actualizamos el tipo de cambio con la fecha de hoy (confirmación)
        for order in self:
            # Obtenemos el nuevo tipo de cambio del día de la confirmación
            new_rate = order._get_exchange_rate_for_date(fields.Date.today())
            # Calculamos el nuevo monto en PEN con el nuevo tipo de cambio
            new_amount_pen = order.amount_total * new_rate
            # Escribimos ambos valores explícitamente para asegurar la actualización
            order.write({
                'acs_type_exchange': new_rate,
                'acs_amount_pen': new_amount_pen,
            })

        result = super().action_confirm()
        for order in self:
            if not order.sequence_order_production:
                order.sequence_order_production = self.env['ir.sequence'].next_by_code(
                    'acs.order.production')
        return result

    @api.depends('sequence_order_production')
    def _compute_manufacturing_order_count(self):
        """Calcula el número de órdenes de fabricación para el smart button."""
        for order in self:
            order.manufacturing_order_count = 1 if order.sequence_order_production else 0

    def action_view_manufacturing_order(self):
        """
        Acción para navegar a la vista de formulario de la orden de fabricación.
        Esta acción es llamada por el smart button.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Fabricación',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('acs_sale_extra_calcs.view_manufacturing_order_form').id,
            'target': 'current',
        }

    def action_print_manufacturing_order(self):
        """Acción para imprimir la orden de fabricación"""
        self.ensure_one()
        return self.env.ref('acs_sale_extra_calcs.action_report_manufacturing_order').report_action(self)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Sobrescribe read_group para manejar correctamente la suma del campo acs_amount_pen
        """
        # Solo interceptamos si se está pidiendo la suma de acs_amount_pen
        if 'acs_amount_pen:sum' in fields:
            # Obtenemos el resultado normal
            result = super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)

            # Para cada grupo, calculamos manualmente la suma
            for group in result:
                if '__domain' in group:
                    group_domain = group['__domain']
                else:
                    group_domain = domain

                # Buscamos los registros del grupo y sumamos manualmente
                records = self.search(group_domain)
                group['acs_amount_pen:sum'] = sum(
                    records.mapped('acs_amount_pen'))

            return result

        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    acs_saleorder_with_paid = fields.Boolean(
        string="Tiene Pago Registrado",
        compute='_compute_acs_saleorder_with_paid',
        store=True,
        help="Verdadero si el pedido tiene al menos una factura con un pago monetario neto (considerando notas de crédito) mayor a cero."
    )

    acs_payment_status_text = fields.Char(
        string="Aprob./No Aprob.",
        compute='_compute_acs_payment_status_text',
        store=True,
    )

    @api.depends('acs_saleorder_with_paid')
    def _compute_acs_payment_status_text(self):
        for order in self:
            if order.acs_saleorder_with_paid:
                order.acs_payment_status_text = 'Aprobado'
            else:
                order.acs_payment_status_text = 'No aprobado'

    @api.depends('invoice_ids.payment_state', 'invoice_ids.line_ids.matched_credit_ids', 'invoice_ids.line_ids.matched_debit_ids')
    def _compute_acs_saleorder_with_paid(self):
        """
        Calcula si un pedido de venta tiene un pago neto positivo.
        Esto se determina sumando todos los pagos monetarios (banco/caja) y restando los reembolsos.
        El campo es Verdadero solo si el monto neto pagado es mayor a cero.
        """
        for order in self:
            total_payment_amount = 0.0
            total_refund_amount = 0.0

            # Filtramos facturas y notas de crédito que no estén canceladas
            moves = order.invoice_ids.filtered(lambda m: m.state != 'cancel')
            customer_invoices = moves.filtered(
                lambda inv: inv.move_type == 'out_invoice'
            )
            credit_notes = moves.filtered(
                lambda inv: inv.move_type == 'out_refund'
            )

            for invoice in customer_invoices:
                receivable_lines = invoice.line_ids.filtered(
                    lambda line: line.account_id.account_type == 'asset_receivable'
                )
                reconciled_lines = receivable_lines.mapped(
                    'matched_credit_ids.credit_move_id')

                for line in reconciled_lines:
                    # Sumamos los pagos monetarios (entradas de dinero)
                    if line.journal_id.type in ('bank', 'cash'):
                        total_payment_amount += line.credit

            for cn in credit_notes:
                receivable_lines = cn.line_ids.filtered(
                    lambda line: line.account_id.account_type == 'asset_receivable'
                )

                # Pagos sobre la nota de crédito (reembolsos)
                # Un reembolso es un 'debit' en la línea 'receivable' de la nota de crédito
                reconciled_debit_lines = receivable_lines.mapped(
                    'matched_debit_ids.debit_move_id')

                for line in reconciled_debit_lines:
                    # Sumamos los reembolsos (salidas de dinero)
                    if line.journal_id.type in ('bank', 'cash'):
                        total_refund_amount += line.debit

            # El pedido tiene un pago válido si el total de pagos recibidos
            # es mayor que el total de reembolsos emitidos.
            # Esto cubre el caso donde un pago es anulado por un reembolso completo.
            order.acs_saleorder_with_paid = total_payment_amount > total_refund_amount

    @api.model
    def find_orders_with_any_payment(self):
        """
        Busca y devuelve los pedidos de venta que tienen al menos una factura
        de cliente asociada con un pago registrado (parcial o total).

        :return: Un recordset de 'sale.order' que cumplen con el criterio.
        """
        # 1. Buscar todas las facturas de cliente que tienen algún pago (parcial, total o en proceso)
        # y que tienen un pedido de venta de origen.
        invoices_with_payment = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ['partial', 'paid', 'in_payment']),
            ('invoice_origin', '!=', False)
        ])

        # 2. Obtener los nombres de los pedidos de venta de origen (ej. 'SO001').
        sale_order_names = invoices_with_payment.mapped('invoice_origin')

        # 3. Buscar los pedidos de venta que coinciden con esos nombres.
        if not sale_order_names:
            # Devuelve un recordset vacío
            return self.env['sale.order'].browse()

        return self.search([('name', 'in', list(set(sale_order_names)))])
