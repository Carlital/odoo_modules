# -*- coding: utf-8 -*-

from odoo import fields, models, _
from librecpe import Servidor

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pe_guide_report_template = fields.Selection([('standard', 'Standard'), ('custom', 'Custom'),('stylized','Stylized')],
                                                "Report Template", related="company_id.pe_guide_report_template",
                                                default='standard', readonly=False)
    def action_eguide_advanced_config_wizard(self):
        self.ensure_one()
        context = dict(self.env.context)
        context['active_id'] = self.ids
        return {
            'name': _('Electronic Guide Advanced'),
            'res_model': 'pe.eguide.advanced.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('l10n_pe_eguide_advanced.view_form_eguide_advanced_wizard_wizard').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }