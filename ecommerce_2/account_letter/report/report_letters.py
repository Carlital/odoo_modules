# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang

class ReportLetters(models.AbstractModel):
    
    _name = "report.account_letter.report_letter_all_document"
    _description = 'Default Description'
    
    def get_total_letter(self, amount_total, currency_id):
        currency_obj = self.env['res.currency'].browse(currency_id)
        return formatLang(self.env, amount_total, currency_obj=currency_obj)
    
    def _get_journal_by_letter(self, letter_ids):
        query = "select journal_id from account_letter where id in %s group by journal_id;"
        self.env.cr.execute(query,[tuple(letter_ids)])
        journals = self.env.cr.dictfetchall()
        journal_ids = []
        for journal in journals:
            journal_ids.append(journal['journal_id'])
        return self.env['account.journal'].browse(journal_ids)
    
    def get_partner_by_journal(self, journal_id, letter_ids):
        query = "select partner_id from account_letter where id in %s and journal_id = %s group by partner_id;"
        self.env.cr.execute(query,[tuple(letter_ids), journal_id])
        partners = self.env.cr.dictfetchall()
        partner_ids = []
        for partner in partners:
            partner_ids.append(partner['partner_id'])
        return self.env['res.partner'].search([('id','in',partner_ids)], order="name ASC")
    
    def get_currency_by_partner(self, partner_id, journal_id,letter_ids):
        query = "select currency_id from account_letter where id in %s and partner_id = %s and journal_id = %s group by currency_id;"
        self.env.cr.execute(query,[tuple(letter_ids), partner_id, journal_id])
        currencies = self.env.cr.dictfetchall()
        currency_ids = []
        for currency in currencies:
            currency_ids.append(currency['currency_id'])
        return currency_ids
    
    def get_letter_by_partner(self, partner_id, journal_id, currency_id, letter_ids):
        partner_ids = self.env['account.letter'].search([('partner_id','=',partner_id),('journal_id','=',journal_id),('currency_id','=',currency_id),('id','in',letter_ids)],
                                          order = "date ASC, date_due ASC")
        return partner_ids
    
    @api.model
    def get_report_values(self, docids, data=None):
        if data == None:
            data = {}
        letters = data.get('letter_ids', [])
        journal_ids = self._get_journal_by_letter(letters) 
        docs = self.env['account.letter.report.wizard'].browse(data['docs'])
        data['journal_ids'] = journal_ids
        data['date_to'] = fields.Date.context_today(self)
        return {'docs': docs, 'data':data, 'letter_ids': letters,
                'get_partner_by_journal': self.get_partner_by_journal, 'get_total_letter': self.get_total_letter,
                'get_currency_by_partner': self.get_currency_by_partner, 'get_letter_by_partner': self.get_letter_by_partner}
