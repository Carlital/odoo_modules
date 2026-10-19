from odoo import api, fields, models, exceptions

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos personalizados
    auto_invoice = fields.Boolean(string='CPE Automático', default=False)
    auto_picking = fields.Boolean(string='Entrega Automática', default=True)
    auto_pay = fields.Boolean(string='Pago Contado', default=True)
    invoice_number = fields.Char(string='CPE #', compute='_compute_invoice_number', store=True)
    cpe_response = fields.Char(string='Respuesta SUNAT', compute='_compute_invoice_number', store=True)
    document_type_display = fields.Char(string='Tipo de CPE', compute='_compute_document_type_display')
    amount = fields.Monetary(string='Monto', readonly=True)
    
    # Relación a las líneas de pago
    payment_line_ids = fields.One2many(
        'sale.order.payment.line',
        'sale_order_id',
        string='Líneas de Pago',
        copy=False
    )
    
    # Campo para mostrar el estado de pago
    payment_status = fields.Selection([
        ('not_paid', 'No Pagado'),
        ('partial', 'Parcialmente Pagado'),
        ('paid', 'Pagado Completamente')
    ], string='Estado de Pago', compute='_compute_payment_status', store=True)

    @api.depends('payment_line_ids', 'payment_line_ids.amount', 'amount_total')
    def _compute_payment_status(self):
        for order in self:
            total_paid = sum(line.amount for line in order.payment_line_ids)
            if not total_paid:
                order.payment_status = 'not_paid'
            elif total_paid >= order.amount_total:
                order.payment_status = 'paid'
            else:
                order.payment_status = 'partial'

    @api.depends('partner_id.vat', 'partner_id.l10n_latam_identification_type_id', 'auto_invoice', 'auto_pay')
    def _compute_document_type_display(self):
        for order in self:
            if not order.auto_invoice:
                order.document_type_display = 'Nota de venta'
                continue

            partner = order.partner_id
            vat = partner.vat or ''
            id_type = partner.l10n_latam_identification_type_id

            if not partner or not id_type:
                order.document_type_display = ''
                continue

            if id_type.name == 'RUC' and len(vat) == 11:                
                order.document_type_display = 'Factura'
            elif id_type.name == 'DNI' and len(vat) == 8:                
                order.document_type_display = 'Boleta de Venta'
            elif id_type.name == 'VAT' and (not vat or len(vat) == 0):                
                order.document_type_display = 'Boleta de Venta'
            else:
                order.document_type_display = 'Indefinido'

    @api.onchange('auto_pay')
    def _onchange_auto_pay(self):
        for order in self:
            if not order.auto_pay:
                order.auto_invoice = False

    def write(self, vals):
        for order in self:
            if 'auto_pay' in vals and not vals['auto_pay'] and 'auto_invoice' not in vals:
                vals['auto_invoice'] = False
            if 'auto_pay' in vals and vals['auto_pay']:
                inmediate_term = self.env['account.payment.term'].search([('inmediate_pay', '=', True)], limit=1)
                if inmediate_term:
                    vals['payment_term_id'] = inmediate_term.id
        return super(SaleOrder, self).write(vals)
        
    def action_confirm(self):
        for order in self:
            # Si auto_pay está activado y no hay líneas de pago configuradas, abrir el wizard
            if order.auto_pay and not order.payment_line_ids and order.state == 'draft' and not self._context.get('skip_payment_wizard'):
                return {
                    'name': 'Configurar Pagos',
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.payment.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_sale_order_id': order.id}
                }

        # Ejecutar la confirmación estándar
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            # Validar picking si auto_picking está activado
            if order.auto_picking and order.picking_ids:
                for picking in order.picking_ids:
                    # No validar si hay productos con lotes/series
                    has_lot_serial = any(line.product_id.tracking in ('lot', 'serial') for line in picking.move_ids)
                    if has_lot_serial:
                        continue
                    # Forzar validación incluso con stock negativo
                    for move in picking.move_ids_without_package:
                        move.quantity = move.product_uom_qty
                    picking.button_validate()

            # Crear y validar factura si auto_invoice está activado
            if order.auto_invoice and order.state == 'sale':
                # Verificar si hay líneas facturables
                if not any(line.qty_to_invoice > 0 for line in order.order_line):
                    raise exceptions.UserError(_('No hay líneas facturables en el pedido. Asegúrese de que las cantidades estén entregadas (si la política de facturación es "Entrega") o que las líneas sean facturables.'))
                invoice = order._create_invoices()
                if invoice:
                    invoice.action_post()
                    order._compute_invoice_number()

        return res

    @api.depends('invoice_ids', 'invoice_ids.name', 'invoice_ids.state')
    def _compute_invoice_number(self):
        for order in self:
            if order.invoice_ids:
                posted_invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
                invoice = posted_invoices[0] if posted_invoices else order.invoice_ids[0]
                order.invoice_number = invoice.name
                try:
                    if hasattr(invoice, 'pe_response'):
                        order.cpe_response = invoice.pe_response
                    else:
                        order.cpe_response = False
                except Exception:
                    order.cpe_response = False
            else:
                order.invoice_number = False
                order.cpe_response = False

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)
        for order in self:
            order.invalidate_recordset(['invoice_number', 'cpe_response'])
        self._compute_invoice_number()
        return moves

    def action_print_invoice(self):
        self.ensure_one()
        if self.invoice_ids:
            invoice = self.invoice_ids[0]
            try:
                report = self.env['ir.actions.report'].search([
                    ('report_name', '=', 'l10n_pe_cpe.report_cpe'),
                    ('model', '=', 'account.move')
                ], limit=1)
                if not report:
                    report = self.env['ir.actions.report'].search([
                        ('model', '=', 'account.move'),
                        ('report_type', '=', 'qweb-pdf')
                    ], limit=1)
                if report:
                    return report.report_action(invoice)
                else:
                    action = self.env.ref('account.account_invoices')
                    if hasattr(action, 'report_action'):
                        return action.report_action(invoice)
                    else:
                        return {
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.move',
                            'view_mode': 'form',
                            'res_id': invoice.id,
                            'target': 'current',
                        }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error al imprimir',
                        'message': f'No se pudo generar el reporte: {str(e)}',
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sin facturas',
                'message': 'No hay facturas asociadas a esta orden de venta.',
                'sticky': False,
                'type': 'warning',
            }
        }

    def action_print_order_ticket(self):
        self.ensure_one()
        try:
            report = self.env['ir.actions.report'].search([
                ('report_name', '=', 'acs_auto_pay_invoice_picking.sale_order_ticket_report_template'),
                ('model', '=', 'sale.order')
            ], limit=1)
            if report:
                return report.report_action(self)
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Reporte no encontrado',
                        'message': 'No se encontró el reporte de ticket para la orden de venta. Verifica que el módulo esté correctamente configurado.',
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error al imprimir',
                    'message': f'No se pudo generar el reporte: {str(e)}',
                    'sticky': False,
                    'type': 'warning',
                }
            }

    def action_print_invoice_ticket(self):
        self.ensure_one()
        if self.invoice_ids:
            invoice = self.invoice_ids[0]
            try:
                report = self.env['ir.actions.report'].search([
                    ('report_name', '=', 'acs_auto_pay_invoice_picking.account_move_ticket_report_template'),
                    ('model', '=', 'account.move')
                ], limit=1)
                if report:
                    return report.report_action(invoice)
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Reporte no encontrado',
                            'message': 'No se encontró el reporte de ticket para la factura. Verifica que el módulo esté correctamente configurado.',
                            'sticky': False,
                            'type': 'warning',
                        }
                    }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error al imprimir',
                        'message': f'No se pudo generar el reporte: {str(e)}',
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sin facturas',
                'message': 'No hay facturas asociadas a esta orden de venta.',
                'sticky': False,
                'type': 'warning',
            }
        }