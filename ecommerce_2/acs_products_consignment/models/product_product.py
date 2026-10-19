from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Campo relacionado para acceder a los clientes de consignación
    consignment_client_ids = fields.Many2many(
        'res.partner',
        related='product_tmpl_id.consignment_client_ids',
        string='Clientes Consignación',
        readonly=True
    )

    # Campo para filtro de cliente de consignación
    consignment_client_id = fields.Many2one(
        'res.partner',
        string='Cliente a Consignar',
        compute='_compute_consignment_client_id',
        search='_search_consignment_client_id',
        store=False
    )

    @api.depends('product_tmpl_id.consignment_client_ids')
    def _compute_consignment_client_id(self):
        for record in self:
            # Toma el primer cliente o False si no hay ninguno
            clients = record.consignment_client_ids
            record.consignment_client_id = clients[0] if clients else False

    def _search_consignment_client_id(self, operator, value):
        if not value:
            return []
        return [('consignment_client_ids', operator, value)]
