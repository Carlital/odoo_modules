from odoo import models, fields, api
from odoo.exceptions import UserError


class PeElectronicGuide(models.Model):
    _inherit = 'pe.electronic.guide'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    guide_line_ids = fields.One2many(
        'pe.electronic.guide.line', 'guide_id', string='Líneas de Guía')
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        domain=[('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')],
        help='Selecciona una factura de cliente en estado publicado'
    )

    @api.model
    def create(self, vals):
        """
        Verifica permisos antes de crear un registro, pero permite creación
        desde stock.picking sin restricciones
        """
        # Verificar si la creación viene desde stock.picking
        context = self.env.context or {}
        from_picking = context.get('from_picking', False)

        # Si NO viene desde picking, verificar permisos del usuario
        if not from_picking:
            user = self.env.user
            if not user.ver_boton_crear_guias:
                raise UserError(
                    "⚠️ Acceso Restringido\n\n"
                    "No tienes permisos para crear guías electrónicas desde esta vista.\n"
                    "Contacta al administrador del sistema si necesitas estos permisos."
                )

        return super(PeElectronicGuide, self).create(vals)

    @api.model
    def default_get(self, fields_list):
        """
        También verificar cuando se abre el formulario de creación,
        pero permitir si viene desde stock.picking
        """
        context = self.env.context or {}
        from_picking = context.get('from_picking', False)

        # Si NO viene desde picking, verificar permisos del usuario
        if not from_picking:
            user = self.env.user
            if not user.ver_boton_crear_guias:
                raise UserError(
                    "⚠️ Acceso Restringido\n\n"
                    "No tienes permisos para crear guías electrónicas desde esta vista.\n"
                    "Contacta al administrador del sistema si necesitas estos permisos."
                )

        return super(PeElectronicGuide, self).default_get(fields_list)


class PeElectronicGuideLine(models.Model):
    _inherit = 'pe.electronic.guide.line'

    guide_id = fields.Many2one(
        'pe.electronic.guide', string='Guía Electrónica')
    product_id = fields.Many2one('product.product', string='Producto')
    product_code = fields.Char(string='Código del Producto')
    description_picking = fields.Char(string='Descripción picking')
    name = fields.Char(string='Descripción', required=True)


class PeElectronicGuideLine(models.Model):
    _inherit = 'pe.electronic.guide.line'

    guide_id = fields.Many2one(
        'pe.electronic.guide', string='Guía Electrónica')
    product_id = fields.Many2one('product.product', string='Producto')
    product_code = fields.Char(string='Código del Producto')
    description_picking = fields.Char(string='Descripción picking')
    name = fields.Char(string='Descripción', required=True)
