from odoo import models, fields, api
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    eguide_ids = fields.One2many(
        'pe.electronic.guide', 'picking_id', string='Guías Electrónicas')

    # Campo computado para mostrar el conteo en el Smart Button
    eguide_count = fields.Integer(
        string='Número de Guías',
        compute='_compute_eguide_count'
    )

    @api.depends('eguide_ids')
    def _compute_eguide_count(self):
        for record in self:
            record.eguide_count = len(record.eguide_ids)

    def action_create_eguide(self):
        self.ensure_one()
        if self.state != 'done':
            raise UserError(
                "Solo se pueden crear guías de pickings validados (estado 'done').")

        # IMPORTANTE: Crear los modelos con contexto especial
        EGuide = self.env['pe.electronic.guide'].with_context(
            from_picking=True)
        EGuideLine = self.env['pe.electronic.guide.line'].with_context(
            from_picking=True)

        # Evitar duplicados
        if self.eguide_ids:
            raise UserError(
                "Ya existen guías electrónicas creadas para este picking.")

        # Crear guía electrónica con los datos principales del picking
        eguide_vals = {
            'partner_id': self.partner_id.id,
            'picking_id': self.id,
        }
        eguide = EGuide.create(eguide_vals)

        # Crear líneas asociadas con los datos de stock.move
        # CORRECCIÓN: usar move_ids en lugar de move_lines (Odoo 18)
        move_lines_vals = []
        for move in self.move_ids:  # Cambiado de move_lines a move_ids
            line_vals = {
                'guide_id': eguide.id,
                # Campo obligatorio
                'name': move.name or f"Línea para {move.product_id.name}",
                'product_id': move.product_id.id,
                'product_code': move.product_id.default_code or '',  # Mapeo del código del producto
                'description_picking': move.name,
                'quantity': move.product_uom_qty,  # Campo obligatorio quantity
                'uom_code': move.product_id.uom_id.pe_unit_code or move.product_id.uom_id.name,
            }
            move_lines_vals.append(line_vals)

        if move_lines_vals:
            EGuideLine.create(move_lines_vals)

        return True

    def action_open_eguide_tree(self):
        self.ensure_one()

        if not self.eguide_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No hay guías electrónicas creadas para este picking.',
                    'type': 'warning',
                }
            }

        # Si solo hay una guía, abrir directamente en vista formulario
        if len(self.eguide_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pe.electronic.guide',
                'res_id': self.eguide_ids[0].id,
                'view_mode': 'form',
                'target': 'current',
                'name': f'Guía Electrónica - {self.name}',
            }

        # Si hay múltiples guías, intentar abrir en vista lista
        return {
            'type': 'ir.actions.act_window',
            'name': f'Guías Electrónicas - {self.name}',
            'res_model': 'pe.electronic.guide',
            'domain': [('id', 'in', self.eguide_ids.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }
