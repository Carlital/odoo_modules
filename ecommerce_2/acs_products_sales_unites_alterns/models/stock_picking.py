import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    has_convertible_products = fields.Boolean(
        string='Tiene Productos Convertibles',
        compute='_compute_has_convertible_products',
        help='Indica si el picking contiene productos convertibles a metros'
    )

    is_converted = fields.Boolean(
        string='Ya Convertido',
        default=False,
        help='Indica si ya se realizó la conversión de este picking'
    )

    conversion_out_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking de Salida Generado',
        help='Picking de salida generado en la conversión'
    )

    conversion_in_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking de Recepción Generado',
        help='Picking de recepción generado en la conversión'
    )

    can_convert = fields.Boolean(
        string='Puede Convertir',
        compute='_compute_can_convert',
        help='Indica si el usuario actual tiene permiso para realizar conversiones'
    )

    @api.depends_context('uid')
    def _compute_can_convert(self):
        _logger = logging.getLogger(__name__)
        current_user = self.env.user

        # Log para depuración
        _logger.info(f"Usuario actual: {current_user.name}")
        _logger.info(
            f"Allow picking conversion: {current_user.allow_picking_conversion}")

        for record in self:
            # Asegurarse de que el campo existe y obtener su valor
            allow_convert = self.env['res.users'].browse(
                current_user.id).allow_picking_conversion
            _logger.info(f"Valor final de allow_convert: {allow_convert}")

            record.can_convert = allow_convert

    @api.depends('move_ids.product_id.is_convertible_to_meter', 'state', 'is_converted')
    def _compute_has_convertible_products(self):
        for picking in self:
            picking.has_convertible_products = (
                picking.picking_type_id.code == 'incoming' and
                picking.state == 'done' and
                not picking.is_converted and
                any(move.product_id.is_convertible_to_meter for move in picking.move_ids)
            )

    def action_convert_to_meters(self):
        """
        Acción principal para convertir productos de peso a metros lineales
        """
        self.ensure_one()

        if self.state != 'done':
            raise UserError(
                _('Este picking debe estar validado (estado Done) para poder ser convertido.'))

        if self.is_converted:
            raise UserError(_('Este picking ya ha sido convertido.'))

        # Obtener productos convertibles
        convertible_moves = self.move_ids.filtered(
            lambda m: m.product_id.is_convertible_to_meter and m.quantity > 0
        )

        if not convertible_moves:
            raise UserError(
                _('No hay movimientos con productos convertibles para procesar.'))

        # Validar que todos los productos tengan configuración completa
        self._validate_conversion_setup(convertible_moves)

        # Crear picking de salida
        out_picking = self._create_conversion_out_picking(convertible_moves)

        # Crear picking de recepción
        in_picking = self._create_conversion_in_picking(convertible_moves)

        # Marcar como convertido
        self.write({
            'is_converted': True,
            'conversion_out_picking_id': out_picking.id,
            'conversion_in_picking_id': in_picking.id
        })

        # Debug: Verificar que el estado se haya cambiado correctamente
        _logger = logging.getLogger(__name__)
        _logger.info(
            f"is_converted después de conversión: {self.is_converted}")
        _logger.info(
            f"Has convertible products: {self.has_convertible_products}")

        # Devolver acción que refresque el registro actual
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'current',
            'context': {
                **self.env.context,
                'default_message': _('Se han creado los pickings de conversión. Picking de salida: %s, Picking de recepción: %s') % (
                    out_picking.name, in_picking.name
                )
            }
        }

        # Los campos computados se recalcularán automáticamente por las dependencias @api.depends

        # Devolver notificación de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Conversión Exitosa'),
                'message': _('Se han creado los pickings de conversión. Picking de salida: %s, Picking de recepción: %s') % (
                    out_picking.name, in_picking.name
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def _validate_conversion_setup(self, convertible_moves):
        """
        Validar que todos los productos tengan la configuración necesaria para la conversión
        """
        for move in convertible_moves:
            product = move.product_id
            if not product.conversion_ratio or product.conversion_ratio <= 0:
                raise ValidationError(
                    _('El producto %s no tiene un ratio de conversión válido.') % product.display_name
                )
            if not product.meter_counterpart_product_id:
                raise ValidationError(
                    _('El producto %s no tiene configurado un producto contraparte en metros.') % product.display_name
                )

    def _create_conversion_out_picking(self, convertible_moves):
        """
        Crear picking de salida para dar salida a los productos en kilos/peso
        """
        # Obtener el tipo de picking de salida
        picking_type_out = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.picking_type_id.warehouse_id.id),
            ('code', '=', 'outgoing')
        ], limit=1)

        if not picking_type_out:
            raise UserError(
                _('No se encontró un tipo de picking de salida en este almacén.'))

        # Crear el picking de salida
        out_picking_vals = {
            'picking_type_id': picking_type_out.id,
            'location_id': self.location_dest_id.id,  # Desde donde llegaron los productos
            'location_dest_id': picking_type_out.default_location_dest_id.id,
            'partner_id': False,  # Sin partner como especificado
            'origin': _('Conversión de %s') % self.name,
            'note': _('Picking de salida generado automáticamente para conversión de productos de peso a metros.'),
        }

        out_picking = self.env['stock.picking'].create(out_picking_vals)

        # Crear los movimientos de salida
        for move in convertible_moves:
            self.env['stock.move'].create({
                'name': _('Conversión: %s') % move.product_id.display_name,
                'product_id': move.product_id.id,
                'product_uom': move.product_uom.id,
                'product_uom_qty': move.quantity,
                'quantity': move.quantity,
                'location_id': out_picking.location_id.id,
                'location_dest_id': out_picking.location_dest_id.id,
                'picking_id': out_picking.id,
                'state': 'draft',
            })

        # Confirmar y validar automáticamente el picking de salida
        out_picking.action_confirm()
        out_picking.action_assign()

        # Establecer quantity automáticamente
        for move in out_picking.move_ids:
            move.quantity = move.product_uom_qty

        out_picking.button_validate()

        return out_picking

    def _create_conversion_in_picking(self, convertible_moves):
        """
        Crear picking de recepción para los productos equivalentes en metros
        """
        # Crear el picking de recepción
        in_picking_vals = {
            # Mismo tipo que el picking original
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.picking_type_id.default_location_src_id.id,
            'location_dest_id': self.location_dest_id.id,
            'partner_id': False,  # Sin partner como especificado
            'origin': _('Conversión de %s') % self.name,
            'note': _('Picking de recepción generado automáticamente para productos convertidos a metros. Debe ser validado manualmente.'),
        }

        in_picking = self.env['stock.picking'].create(in_picking_vals)

        # Crear los movimientos de recepción con productos en metros
        for move in convertible_moves:
            product_meters = move.product_id.meter_counterpart_product_id
            converted_quantity = move.quantity / move.product_id.conversion_ratio

            self.env['stock.move'].create({
                'name': _('Conversión: %s') % product_meters.display_name,
                'product_id': product_meters.id,
                'product_uom': product_meters.uom_id.id,
                'product_uom_qty': converted_quantity,
                'location_id': in_picking.location_id.id,
                'location_dest_id': in_picking.location_dest_id.id,
                'picking_id': in_picking.id,
                'state': 'draft',
            })

        # Confirmar el picking pero NO validarlo automáticamente
        in_picking.action_confirm()
        in_picking.action_assign()

        return in_picking

    def action_view_conversion_pickings(self):
        """
        Acción para ver los pickings generados en la conversión
        """
        self.ensure_one()

        picking_ids = []
        if self.conversion_out_picking_id:
            picking_ids.append(self.conversion_out_picking_id.id)
        if self.conversion_in_picking_id:
            picking_ids.append(self.conversion_in_picking_id.id)

        if not picking_ids:
            raise UserError(_('No hay pickings de conversión generados.'))

        return {
            'name': _('Pickings de Conversión'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', picking_ids)],
            'context': dict(self.env.context),
            'target': 'current',
        }

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}

        # Aseguramos que estos campos se reinicien al duplicar
        default.update({
            'is_converted': False,
            'conversion_out_picking_id': False,
            'conversion_in_picking_id': False,
        })

        return super(StockPicking, self).copy(default)
