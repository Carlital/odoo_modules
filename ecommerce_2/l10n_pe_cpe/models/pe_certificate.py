# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import timedelta, datetime

class PeCertificate(models.Model):
    _name = 'pe.certificate'
    _description = 'Peruvian Certificate Manager'

    name = fields.Char("Name", required=True)
    private_key = fields.Text("Private key", required=True)
    public_key = fields.Text("Public key", required=True)
    start_date = fields.Date("Start Date", required=True, default=fields.Date.today)
    end_date = fields.Date("End Date", required=True, default=datetime.now().replace(year=datetime.now().year+1).date())
    # company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False)

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancelled(self):
        self.write({'state': 'cancel'})

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            self.end_date = self.start_date + timedelta(days=365)