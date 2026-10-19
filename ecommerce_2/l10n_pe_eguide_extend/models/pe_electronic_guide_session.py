# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class PeElectronicGuideSession(models.Model):
    _name = "pe.electronic.guide.session"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Electronic Guide Session"

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('pe.electronic.guide.session'))
    name = fields.Char("Name", required=True)
    sequence_id = fields.Many2one('ir.sequence', 'Sequence', readonly=True)
    branch_id = fields.Many2one("pe.electronic.guide.branch", "Branch", domain="[('company_id','=',company_id)]", required="True")
    user_ids = fields.Many2many("res.users", "pe_electronic_guide_session_users_rel", 'session_id', 'user_id', string="Users")
    active = fields.Boolean("Active", default=True)

    @api.model
    def _create_sequence(self, company_id, prefix):
        sequence_id = self.env['ir.sequence'].search([('prefix','=',"%s-" % prefix),('company_id','=',company_id)], limit=1)
        if not sequence_id:
            vals = {}
            vals['name'] = 'Electronic Guide %s' % prefix
            vals['company_id'] = company_id
            vals['prefix'] = "%s-" % prefix
            vals['implementation'] = 'no_gap'
            vals['padding'] = 5
            sequence_id = self.env['ir.sequence'].sudo().create(vals)
        return sequence_id.id

    @api.constrains('name')
    def _check_name(self):
        for session_id in self:
            if not re.match(r'^(T){1}[A-Z0-9]{3}$', session_id.name):
                raise ValidationError("Ingrese un prefijo para la guia correcto por ejemplo T001")
            if self.search([('name','=',session_id.name),('company_id','=',session_id.company_id.id),
                            ('id','!=',session_id.id)]):
                raise ValidationError("El prefijo debe ser unico por compania")

    @api.model
    def create(self, vals):
        res = super(PeElectronicGuideSession, self).create(vals)
        res.sequence_id = self._create_sequence(res.company_id.id, res.name)
        return res