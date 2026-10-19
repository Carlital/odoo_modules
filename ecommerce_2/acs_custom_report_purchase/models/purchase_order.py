# -*- coding: utf-8 -*-
from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    acs_contact_provider = fields.Many2one(
        'res.partner',
        string='Contacto del Proveedor',
        domain="[('parent_id', '=', partner_id), ('type', '=', 'contact')]",
        help="Seleccione un contacto asociado al proveedor."
    )

    other_reception_street = fields.Boolean(
        string='Otra dirección de recepción',
        default=False
    )
    other_reception_input = fields.Char(
        string='Dirección de recepción'
    )
