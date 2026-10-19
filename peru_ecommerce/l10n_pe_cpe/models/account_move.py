# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
import tempfile
from base64 import encodebytes
import json
from datetime import datetime, date, timedelta
from io import BytesIO
from num2words import num2words
import re
try:
    import qrcode
    qr_mod = True
except:
    qr_mod = False

class AccountMove(models.Model):
    _inherit = "account.move"
    
    pe_invoice_date = fields.Datetime("Invoice Date Time", readonly=True, copy = False)
    pe_operation_type = fields.Selection("_get_pe_sunat_transaction", string= "Type of operation", default="0101")
    pe_voided_id= fields.Many2one("pe.cpe.ra", "Voided Document", copy=False)
    pe_summary_id = fields.Many2one("pe.cpe.rc", "Summary Document", copy=False)
    
    pe_cpe_id = fields.Many2one("account.edi.document", "CPE", compute = "_compute_pe_edi_detail", store=True, copy=False)
    pe_digest = fields.Char("Digest", compute = "_compute_pe_edi_detail", store=True, copy=False)
    pe_response = fields.Char("Response", compute = "_compute_pe_edi_detail", store=True, copy=False)
    pe_return_code = fields.Selection("_get_return_code", string= "Return Code",  compute="_compute_pe_edi_detail", store=True, copy=False)
    pe_response_id = fields.Many2one("ir.attachment", "XML Response", compute="_compute_pe_edi_detail", store=True, copy=False)
    pe_attachment_id = fields.Many2one("ir.attachment", "XML Response", compute="_compute_pe_edi_detail", store=True, copy=False)
    
    pe_qr_code = fields.Binary("QR Code", compute="_compute_pe_qr_code")
    pe_is_cpe = fields.Boolean("Is CPE", compute="_compute_pe_is_cpe", store=True, copy=False)
    pe_legend_ids = fields.One2many("pe.legend", "move_id", "Legend")
    pe_invoice_sent = fields.Boolean(readonly=True, default=False, copy=False, help="It indicates that the invoice has been sent.")
    
    pe_condition_code = fields.Selection("_get_pe_condition_code", "Condition Code", default='1')
    pe_reversed_entry_id = fields.Many2one('account.move', string="Reversal of Credit/Debit Note",
                                           compute="_cumpute_pe_reversed_entry_id",
                                           inverse="_inverse_pe_reversed_entry_id")

    pe_related_document_ids = fields.One2many("pe.related.document", "move_id", "Related Document")

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        result = super()._get_l10n_latam_documents_domain()
        if self.company_id.country_id.code != "PE" or not self.journal_id.l10n_latam_use_documents or self.journal_id.type != "sale":
            return result
        if self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '0' and self.pe_operation_type and self.pe_operation_type[:2] == '02':
            result=result[:-1] #('id', 'in', (self.env.ref('l10n_pe.document_type01') | self.env.ref('l10n_pe.document_type07') | self.env.ref('l10n_pe.document_type08')).ids)
        return result

    @api.depends('journal_id', 'partner_id', 'company_id', 'move_type', 'debit_origin_id', 'pe_operation_type')
    def _compute_l10n_latam_available_document_types(self):
        return super(AccountMove, self)._compute_l10n_latam_available_document_types()

    @api.depends('debit_origin_id', 'reversed_entry_id')
    def _cumpute_pe_reversed_entry_id(self):
        for move in self:
            if move.is_sale_document():
                if move.pe_invoice_code in ['07']:
                    move.pe_reversed_entry_id = move.reversed_entry_id.id
                elif move.pe_invoice_code in ['08']:
                    move.pe_reversed_entry_id = move.debit_origin_id.id
                else:
                    move.pe_reversed_entry_id = False
            else:
                move.pe_reversed_entry_id = False

    def _inverse_pe_reversed_entry_id(self):
        for move in self:
            if move.is_sale_document():
                if move.pe_invoice_code in ['07']:
                    move.reversed_entry_id = move.pe_reversed_entry_id.id
                elif move.pe_invoice_code in ['08']:
                    move.debit_origin_id = move.pe_reversed_entry_id.id

    @api.depends('edi_document_ids.pe_digest',
                 'edi_document_ids.pe_response',
                 'edi_document_ids.pe_return_code',
                 'edi_document_ids.pe_response_id',
                 'edi_document_ids.attachment_id')
    def _compute_pe_edi_detail(self):
        for move in self.filtered(lambda s: s.country_code=='PE'):
            edi_document_ids = move.edi_document_ids.filtered(lambda s: s.edi_format_id.code == 'pe_cpe')
            edi_document_id = edi_document_ids and edi_document_ids[0] or False
            move.pe_cpe_id = edi_document_id and edi_document_id[0] or False
            move.pe_digest = edi_document_id and  edi_document_id.pe_digest or False
            move.pe_response = edi_document_id and  edi_document_id.pe_response or False
            move.pe_return_code = edi_document_id and edi_document_id.pe_return_code or False
            move.pe_response_id = edi_document_id and edi_document_id.pe_response_id.id or False
            move.pe_attachment_id = edi_document_id and edi_document_id.attachment_id.id or False
    
    @api.depends('journal_id', 'journal_id.edi_format_ids')
    def _compute_pe_is_cpe(self):
        for move in self.filtered(lambda s: s.country_code=='PE'):
            move.pe_is_cpe = bool(move.journal_id.edi_format_ids.filtered(lambda j: j.code == 'pe_cpe'))
    
    @api.model
    def _get_pe_condition_code(self):
        return self.env['pe.catalog.19'].get_selection()
    
    def get_pe_invoice_name(self):
        self.ensure_one()
        return self.env['pe.catalog.01'].get_by_code(self.pe_invoice_code).name
    
    @api.depends("partner_id", "pe_is_cpe", "invoice_date")
    def _compute_pe_qr_code(self):
        for move in self.filtered(lambda s: s.country_code=='PE'):
            res=[]
            if move.name and move.pe_is_cpe and move.pe_cpe_id and qr_mod:
                res.append(move.company_id.vat or "-")
                res.append(move.pe_invoice_code or '')
                res.append(move.name.split("-")[0] or '')
                res.append(move.name.split("-")[-1] or '')
                res.append(str(move.amount_tax))
                res.append(str(move.amount_total))
                res.append(fields.Date.to_string(move.invoice_date))
                res.append(move.partner_id.pe_doc_type or "-")
                res.append(move.partner_id.pe_doc_number or "-")
                res.append("")
                qr_string='|'.join(res)
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                image = qr.make_image()
                tmpf = BytesIO()
                image.save(tmpf,'png')
                move.pe_qr_code = encodebytes(tmpf.getvalue())
            else:
                move.pe_qr_code = False
    
    @api.model
    def _get_return_code(self):
        return self.env['pe.catalog.return'].get_selection()
    
    @api.model
    def _get_pe_sunat_transaction(self):
        return self.env['pe.catalog.51'].get_selection()
            
    def get_legend(self):
        self.ensure_one()
        self.pe_legend_ids.filtered(lambda ln: ln.is_auto == True or ln.code in ['1000','1002','2001','2002']).unlink()
        res = []
        amount_total = round(self.amount_total, self.currency_id.decimal_places or 2)
        amount = int(amount_total)
        cents = str(int(round(round((amount_total - amount), self.currency_id.decimal_places or 2)*100))).zfill(2)
        vals = {}
        vals['code'] = '1000'
        vals['name'] = num2words(amount, lang='es').upper() + " Y %s/100 %s" %(cents, (self.currency_id.currency_unit_label or self.currency_id.name).upper()) 
        vals['is_auto'] = True
        res.append((0,0, vals))
        if self.invoice_line_ids.filtered(lambda ln: ln.price_total == 0.0 and ln.display_type not in ['line_section', 'line_note']):
            vals = {}
            vals['code'] = '1002'
            vals['name'] = self.env['pe.catalog.52'].get_by_code('1002').name
            vals['is_auto'] = True
            res.append((0,0, vals))
        if self.pe_subject_detraction and self.pe_detraction_amount > 0.0:# and self.amount_total>=700:
            vals = {}
            vals['code'] = '2006'
            vals['name'] = self.env['pe.catalog.52'].get_by_code('2006').name
            vals['is_auto'] = True
            res.append((0,0, vals))
        if self.company_id.pe_is_exonerated:
            if self.invoice_line_ids.filtered(lambda ln: ln.product_id.type not in ['service'] or not ln.product_id):
                vals = {}
                vals['code'] = '2001'
                vals['name'] = self.env['pe.catalog.52'].get_by_code('2001').name
                vals['is_auto'] = True
                res.append((0,0, vals))
            if self.invoice_line_ids.filtered(lambda ln: ln.product_id.type in ['service']):
                vals = {}
                vals['code'] = '2002'
                vals['name'] = self.env['pe.catalog.52'].get_by_code('2002').name
                vals['is_auto'] = True
                res.append((0,0, vals))
        return self.write({'pe_legend_ids': res})
        
    def get_operations(self):
        for move in self:
            taxes = 0.0
            exonerated = 0.0
            unaffected = 0.0
            exports = 0.0
            free = 0.0
            for line in move.invoice_line_ids.filtered(lambda ln: ln.quantity>0.0):
                if line.pe_type_affectation in ['10']:
                    taxes+=line._get_pe_all_taxes().get('price_subtotal', 0.0)
                elif line.pe_type_affectation in ['20']:
                    exonerated+=line._get_pe_all_taxes().get('price_subtotal', 0.0)
                elif line.pe_type_affectation in ['30']:
                    unaffected+=line._get_pe_all_taxes().get('price_subtotal', 0.0)
                elif line.pe_type_affectation in ['40']:
                    exports+=line._get_pe_all_taxes().get('price_subtotal', 0.0)
                elif line.pe_type_affectation not in ['10', '20', '30', '40']:
                    free+=line._get_pe_all_taxes(discount=0.0).get('price_subtotal', 0.0)
            if taxes> 0.0:
                self.env['pe.operations'].create({'move_id':move.id,"code":"1","amount":taxes})
            if exonerated> 0.0:
                self.env['pe.operations'].create({'move_id':move.id,"code":"2","amount":exonerated})
            if unaffected> 0.0:
                self.env['pe.operations'].create({'move_id':move.id,"code":"3","amount":unaffected})
            if exports> 0.0:
                self.env['pe.operations'].create({'move_id':move.id,"code":"4","amount":exports})
            if free> 0.0:
                self.env['pe.operations'].create({'move_id':move.id,"code":"5","amount":free})
                 
    
    def _post(self, soft=True):
        for move in self:
            if move.is_invoice(include_receipts=True) and move.pe_is_cpe:
                move.get_legend()
                record = self.with_context(tz = "America/Lima")
                dt = fields.Datetime.context_timestamp(record, datetime.now())
                local_date = dt.date() #fields.Date.to_string(fields.Date.from_string(dt))
                invoice_date = move.invoice_date or fields.Date.context_today(record)
                if (local_date == invoice_date):
                    move.pe_invoice_date= fields.Datetime.to_string(dt)
                else:
                    move.pe_invoice_date = fields.Date.to_string(invoice_date) + ' 23:55:00'
        res =  super(AccountMove, self)._post(soft=soft)
        return res
                
    def _pe_cpe_document_name(self, move_id=None):
        self.ensure_one()
        move_id = move_id or self
        ruc= move_id.company_id.partner_id.pe_doc_number
        doc_code= "-%s" % move_id.pe_invoice_code
        number = move_id.l10n_latam_document_number
        return "%s%s-%s" %(ruc, doc_code, number)
    
    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_sunat_code(self):
        self.ensure_one()
        move = self
        tax_lines = self.invoice_line_ids.filtered(lambda line: line.tax_line_id and line.tax_line_id.pe_tax_type)
        res = {}
        done_taxes = set()
        
        for line in self.invoice_line_ids.filtered(lambda line: line.display_type not in ['line_section', 'line_note']):
            taxes = line._get_pe_all_taxes(taxes=line.tax_ids)
            if line.pe_type_affectation in ['10','20', '30', '40']:
                for tax in taxes.get('taxes', []):
                    tax_id = self.env['account.tax'].browse(tax['id'])
                    res.setdefault(tax_id.l10n_pe_edi_tax_code or '9999', {'base': 0.0, 'amount': 0.0})
                    res[tax_id.l10n_pe_edi_tax_code]['amount'] += tax.get('amount', 0.0)
                    res[tax_id.l10n_pe_edi_tax_code]['tax_id'] = tax_id.id
                    tax_key_add_base = tuple(tax_id.ids)
                    if tax_id.l10n_pe_edi_tax_code == '7152':
                        res[tax_id.l10n_pe_edi_tax_code]['base'] += tax.get('base', 0.0) #int(tax.get('amount', 0.0)/(line.quantity or 1))
                    else:
                        res[tax_id.l10n_pe_edi_tax_code]['base'] += tax.get('base', 0.0)
                    done_taxes.add(tax_key_add_base)
            if line.pe_type_affectation not in ['10','20', '30', '40']:
                taxes = line._get_pe_all_taxes(taxes=line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code not in['9996']), discount = 0.0)
                tax_id = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996'])
                for tax in taxes.get('taxes', []):
                    res.setdefault(tax_id.l10n_pe_edi_tax_code, {'base': 0.0, 'amount': 0.0})
                    res[tax_id.l10n_pe_edi_tax_code]['amount'] += tax.get('amount', 0.0)
                    res[tax_id.l10n_pe_edi_tax_code]['tax_id'] = tax_id.id
                    tax_key_add_base = tuple(tax_id.ids)
                    res[tax_id.l10n_pe_edi_tax_code]['base'] += tax.get('base', 0.0)
                    done_taxes.add(tax_key_add_base)
        res = sorted(res.items())
        return res
    
    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for move in self:
            if move.pe_is_cpe:
                if move.pe_cpe_id.state == 'sent' and move.pe_invoice_code=="03"  or move.reversed_entry_id.pe_invoice_code=="03"\
                   or move.debit_origin_id.pe_invoice_code=="03":
                    move.pe_condition_code = '2'
                if move.pe_cpe_id.state in ['sent'] and not move.env.context.get('pe_annul_document'):
                    raise UserError(_('You can not reset the draft a document sent to the sunat'))
                if not move.env.context.get('pe_annul_document'):
                    # move.pe_cpe_id.document = False
                    move.pe_summary_id = False
                    move.pe_voided_id = False
        return res
    
    def _button_pe_annul(self):
        for move in self:
            if move.pe_is_cpe:
                if move.company_id.pe_ws_server in  ['nubefact_pse']:
                    voided_id = self.env['pe.cpe.ra'].get_cpe_async(move.id)
                    move.pe_voided_id = voided_id.id
                    voided_id.action_generate()
                    try:
                        voided_id.action_sent()
                    except Exception:
                        pass
                else:
                    if move.pe_invoice_code=="03"  or move.reversed_entry_id.pe_invoice_code=="03" or \
                       move.debit_origin_id.pe_invoice_code=="03": 
                        if move.pe_summary_id.state == 'sent':
                            move.pe_condition_code = '3'
                            pe_summary_id=self.env['pe.cpe.rc'].get_cpe_async(move.id)
                            move.pe_summary_id=pe_summary_id.id
                    else:
                        voided_id = self.env['pe.cpe.ra'].get_cpe_async(move.id)
                        move.pe_voided_id = voided_id.id
    
    def button_cancel_posted_moves(self):
        res = super(AccountMove, self).button_cancel_posted_moves()
        self._button_pe_annul()
        return res
    
    def button_pe_annul(self):
        self.button_cancel_posted_moves()
        res = super(AccountMove, self).button_pe_annul()
        return res

    # def action_invoice_sent(self):
    #     res = super(AccountMove, self).action_invoice_sent()
    #     context = dict(res.get('context'))
    #     if self.pe_is_cpe and self.pe_cpe_id:
    #         attachment_ids = []
    #         if self.pe_cpe_id.attachment_id:
    #             attach_id = self.pe_cpe_id.attachment_id.copy()
    #             attach_id.write({'res_model':'mail.compose.message', 'res_id':'0'})
    #             attachment_ids.append(attach_id.id)
    #         if self.pe_cpe_id.pe_response_id:
    #             attach_id = self.pe_cpe_id.pe_response_id.copy()
    #             attach_id.write({'res_model':'mail.compose.message', 'res_id':'0'})
    #             attachment_ids.append(attach_id.id)
    #         context['default_attachment_ids']=[(6, 0, attachment_ids)]
    #         res['context'] = context
    #     return res

    def action_send_mass_mail(self):
        today= fields.Date.to_string(fields.Date.context_today(self))
        invoice_ids = self.search([('state', 'not in', ['draft', 'cancel']), ('invoice_date', '=', today), ('pe_is_cpe', '=', True)])
        for invoice_id in invoice_ids:
            if invoice_id.partner_id.email and not invoice_id.pe_invoice_sent and invoice_id.pe_cpe_id:
                attachments=[]
                if invoice_id.pe_cpe_id.attachment_id:
                    attachments.append((invoice_id.pe_cpe_id.attachment_id.name,
                                        invoice_id.pe_cpe_id.attachment_id.datas))
                if invoice_id.pe_cpe_id.pe_response_id:
                    attachments.append((invoice_id.pe_cpe_id.pe_response_id.name,
                                        invoice_id.pe_cpe_id.pe_response_id.datas))
                template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
                if not template:
                    continue
                template.send_mail(invoice_id.id, force_send=True, email_values={'attachments': attachments})
                invoice_id.pe_invoice_sent = True

    def get_public_cpe(self):
        self.ensure_one()
        res = {}
        if self.journal_id.pe_is_cpe and self.pe_cpe_id:
            result_pdf, type = self.env['ir.actions.report']._get_report_from_name('account.report_invoice').render_qweb_pdf(self.ids)
            res['datas_sign'] =str(self.pe_cpe_id.datas_sign,"utf-8")
            res['datas_invoice'] = str(encodebytes(result_pdf),"utf-8")
            res['name'] = self.pe_cpe_id.get_document_name()
        return res

    def get_pe_amount_vals(self):
        self.ensure_one()
        currency = self.currency_id
        vals = self.tax_totals
        vals['formatted_pe_detraction_amount'] = self.pe_detraction_amount and \
                                       formatLang(self.env, self.pe_detraction_amount, currency_obj=self.company_currency_id) or False
        vals['formatted_pe_retention_amount'] = self.pe_retention_amount and \
                                      formatLang(self.env, self.pe_retention_amount, currency_obj=currency) or False

        return vals

    @api.onchange('invoice_line_ids', 'invoice_line_ids.product_id', 'amount_total', 'invoice_date')
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'amount_total', 'invoice_date')
    def _onchange_invoice_pe_detractions(self):
        for line_id in self.line_ids.filtered(
                lambda s: s.product_id.pe_subject_detraction and s.move_id.move_type in ['out_invoice', 'out_refund']):
            catalog_id = self.env['pe.catalog.54'].get_by_code(line_id.product_id.pe_subject_detraction)
            amount = self.currency_id._convert(self.amount_total,
                                               self.env.ref('base.PEN'), self.company_id,
                                               self.invoice_date or fields.Date.context_today(self))
            if amount > 700:
                if not self.pe_subject_detraction and catalog_id:
                    self.pe_subject_detraction = catalog_id.code
                elif self.pe_subject_detraction and catalog_id:
                    catalog2_id = self.env['pe.catalog.54'].get_by_code(self.pe_subject_detraction)
                    if catalog2_id.rate > catalog_id.rate:
                        self.pe_subject_detraction = catalog2_id.code
                self.pe_operation_type = '1001'
            else:
                self.pe_subject_detraction = False
                self.pe_operation_type = '0101'
        return {}

    @api.onchange('pe_subject_detraction')
    @api.depends('pe_subject_detraction')
    def onchange_pe_subject_detraction(self):
        amount = self.currency_id._convert(self.amount_total,
                                           self.env.ref('base.PEN'), self.company_id,
                                           self.invoice_date or fields.Date.context_today(self))
        if amount > 700 and self.pe_subject_detraction:
            self.pe_operation_type = '1001'
        else:
            self.pe_operation_type = '0101'

    def _get_pe_partner_document_code(self):
        self.ensure_one()
        if self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code in ['1', '6']:
            return self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '1' and 'DNI' or 'RUC'
        elif self.partner_id.l10n_latam_identification_type_id:
            return self.partner_id.l10n_latam_identification_type_id.name
        else:
            return False

    def _get_name_invoice_report(self):
        res = super(AccountMove, self)._get_name_invoice_report()
        if self.pe_is_cpe:
            res = 'l10n_pe_cpe.report_cpe_document'
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_pe_all_taxes(self, price_unit=None, quantity=None, discount=None, move_type=None, currency=None, 
                          product=None, partner=None, taxes=None, company=None, date=None):
        self.ensure_one()
        price_unit=price_unit or self.price_unit
        quantity=quantity or self.quantity
        if discount == None:
            discount=self.discount    
        currency=currency or self.currency_id
        product=product or self.product_id
        partner=partner or self.partner_id
        taxes=taxes or self.tax_ids
        move_type=move_type or self.move_id.move_type
        
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount

        res = {}
        if taxes.filtered(lambda  tax: tax.l10n_pe_edi_tax_code not in ['9996']):
            res = taxes.compute_all(price_unit_wo_discount, quantity=quantity, currency=currency, product=product,
                                                  partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
        elif taxes.filtered(lambda  tax: tax.l10n_pe_edi_tax_code in ['9996']):
            res = taxes.filtered(lambda  tax: tax.l10n_pe_edi_tax_code not in ['9996']).compute_all(price_unit, quantity=quantity, currency=currency, product=product,
                                                  partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            free_tax = taxes.filtered(lambda  tax: tax.l10n_pe_edi_tax_code in ['9996'])[0]
            taxes_vals = res.get('taxes', [])
            free_taxes = []
            for taxes_val in taxes_vals:
                taxes_val['free_id'] = free_tax.id
                free_taxes.append(taxes_val)
            res['taxes'] = free_taxes
        return res

