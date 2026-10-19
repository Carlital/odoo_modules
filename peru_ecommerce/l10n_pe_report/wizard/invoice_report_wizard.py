# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class InvoiceReportWizard(models.TransientModel):
    _name = "pe.invoice.report.wizard"
    _description = "Inovoice Report"
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    start_date = fields.Date("Start Date", default = fields.Date.context_today)
    end_date = fields.Date("End Date", default = fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner', string = 'Partner')
    user_ids = fields.Many2many('res.users', string = 'Salesperson')
    show_lines = fields.Boolean("Show Lines", default = True)
    
    def _prepare_sale_report(self):
        self.ensure_one()
        querry = []
        vals = {}
        if self.company_id:
            querry.append(('company_id','=', self.company_id.id))
        if self.start_date:
            querry.append(('invoice_date','>=', self.start_date))
        if self.end_date:
            querry.append(('invoice_date','<=', self.end_date))
        if self.partner_ids:
            querry.append(('partner_id','in', self.partner_ids.ids))
        if self.user_ids:
            querry.append(('user_id','in', self.user_ids.ids))
        #elif self.team_ids and self.report_by == 'report_team':
        #    querry.append(('team_id','in', self.team_ids.ids))
        querry.append(('name', '!=', '/'))
        querry.append(('state', 'in', ['posted','cancel']))
        querry.append(('move_type', 'in', ['out_invoice', 'out_refund']))
        invoice_ids = self.env['account.move'].search(querry)
        if not invoice_ids:
            raise ValidationError(_("There are no sales orders"))
        vals['start_date'] = self.start_date
        vals['end_date'] = self.end_date
        vals['invoice_ids'] = invoice_ids.ids
        vals['invoice_repor_id'] = self.id
        vals['show_lines'] = self.show_lines
        return vals
    
    def button_export_xlsx_sunat(self):
        self.ensure_one()
        data =  {}
        return self.env.ref('l10n_pe_report.action_report_invoice_report_sunat_xlsx').report_action(self, data=data)
    