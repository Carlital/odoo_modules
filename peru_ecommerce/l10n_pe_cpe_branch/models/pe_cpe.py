# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

            
class PeCpeRC(models.Model):
    _inherit = "pe.cpe.rc"
    
    branch_id = fields.Many2one('res.company.branch', 'Branch',
                                readonly=True)
    
    def _get_branch(self, invoice_id):
        if invoice_id.branch_id:
            return {'pe_branch_code':invoice_id.branch_id.pe_branch_code or '0000', 
                    'branch_id': invoice_id.branch_id.id}
        else:
            return super(PeCpeRC, self)._get_branch(invoice_id)
    
    
class PeCpeRA(models.Model):
    _inherit = "pe.cpe.ra"    
    
    branch_id = fields.Many2one('res.company.branch', 'Branch',
                                readonly=True)
    
    def _get_branch(self, invoice_id):
        if invoice_id.branch_id.pe_branch_code:
            return {'pe_branch_code':invoice_id.branch_id.pe_branch_code or '0000', 
                    'branch_id': invoice_id.branch_id.id}
        else:
            return super(PeCpeRA, self)._get_branch(invoice_id)

class PeSunatEguide(models.Model):
    _inherit = 'pe.eguide'

    branch_id = fields.Many2one('res.company.branch', 'Branch',
                                readonly=True)

    @api.model
    def create_from_stock(self, picking_id):
        res = super(PeSunatEguide, self).create_from_stock(picking_id)
        res.branch_id = picking_id.pe_warehouse_id.pe_branch_id.id
        return res