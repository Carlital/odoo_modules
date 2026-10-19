from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    consignment_client_ids = fields.Many2many(
        'res.partner',
        'product_template_consignment_rel',  # Nombre explícito de la tabla relacional
        'product_tmpl_id',
        'partner_id',
        string='Cliente Consignación',
        domain=[('is_company', '=', True), ('customer_rank', '>', 0)],  # Solo clientes
        help='Clientes que pueden recibir este producto en consignación'
    )