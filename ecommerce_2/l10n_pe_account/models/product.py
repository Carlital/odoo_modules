# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = "product.category"
    
    pe_unspsc_code = fields.Char("UNSPSC Code")
    pe_code = fields.Selection("_get_pe_code", "Código del catálogo", default="9",
                               help="Código del catálogo utilizado. Sólo se podrá incluir las opciones 3 y 9 de la tabla 13.")
    pe_type = fields.Selection("_get_pe_type", "Tipo de existencia", default = "01")

    @api.model
    def _get_pe_code(self):
        return self.env['pe.table.13'].get_selection()

    @api.model
    def _get_pe_type(self):
        return self.env['pe.table.05'].get_selection()

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    pe_unspsc_code = fields.Char("UNSPSC Code")
    pe_product_type = fields.Selection([("discount","Discount"),
                                        ("charge","Charge"),
                                        ("prepayment", "Prepayment")], "Special Product Type")
    pe_subject_detraction = fields.Selection('_get_pe_subject_detraction', 'Subject to Detraction')

    @api.model
    def _get_pe_subject_detraction(self):
        return self.env['pe.catalog.54'].get_selection()
