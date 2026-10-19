# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountLetterReportWizard(models.TransientModel):
    
    _name = "account.letter.report.wizard"
    _description = 'Default Description'
    
    partner_ids = fields.Many2many('res.partner', 'account_letter_report_wizard_partner_rel', 'partner_id', 'wizard_id', "Partner")
    
    
    def _prepare_report(self):
        self.ensure_one()
        res = [('state','not in',['draft','cancel', 'accepted'])]
        if self.partner_ids:
            res.append(('partner_id','in',self.partner_ids.ids))
        letter_ids = self.env['account.letter'].search(res)
        return {'letter_ids':letter_ids.ids, 'docs': self.ids}
    
    
    def button_export_pdf(self):
        self.ensure_one()
        data =  self._prepare_report()
        return self.env.ref('account_letter.action_report_letter_all_document').with_context(landscape=True).report_action(self, data=data)