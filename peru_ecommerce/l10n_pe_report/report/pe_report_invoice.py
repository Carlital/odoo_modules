
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from datetime import datetime

class PartnerXlsx(models.AbstractModel):
    _name = 'report.l10n_pe_report.action_report_invoice_report_sunat_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def _op_total(self, invoice_id):
        op_gravada = 0.0
        op_exonerada = 0.0
        op_inafecta = 0.0
        op_icbper = 0.0
        op_icbper_amount = 0.0
        igv_amount = 0.0
        for line_id in invoice_id.line_ids.filtered(lambda l: l.tax_line_id.pe_tax_type.code in ['1000']):
            op_gravada+=line_id.tax_base_amount
            igv_amount+=abs(line_id.balance)
        for line_id in invoice_id.line_ids.filtered(lambda l: l.tax_line_id.pe_tax_type.code in ['7152']):
            op_icbper += line_id.tax_base_amount
            op_icbper_amount += (abs(line_id.balance) / line_id.tax_line_id.amount)
        for line_id in invoice_id.invoice_line_ids.filtered(lambda s: s.pe_type_affectation in ['20', '40']):
            op_exonerada+=line_id.price_total
        for line_id in invoice_id.invoice_line_ids.filtered(lambda s: s.pe_type_affectation in ['30']):
            op_inafecta+=line_id.price_total
        return {'op_gravada':op_gravada,'op_exonerada':op_exonerada,'op_inafecta':op_inafecta, 'op_icbper':op_icbper, 'op_icbper_amount':op_icbper_amount,
                'igv_amount':igv_amount}
    
    @api.model
    def get_report_values(self, docids, data=None):
        invoice_repor = self.env['pe.invoice.report.wizard'].browse(data['invoice_repor_id'])
        invoice_ids = self.env['account.invoice'].browse((data['invoice_ids']))
        docs = invoice_ids
        data['currency_ids'] = invoice_ids.mapped('currency_id')
        data['invoice_ids'] = invoice_ids
        data['journal_ids'] = invoice_ids.mapped('journal_id')
        return {'docs': invoice_repor, 'data':data, 'invoice_report': self}

    def get_workbook_options(self):
        return {'constant_memory': True}

    def generate_xlsx_report(self, workbook, data, objs):
        digit2 = workbook.add_format({'num_format': '0.00'})
        date = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        #digit8 = workbook.add_format({'num_format': '0.00000000'})
        sheet = workbook.add_worksheet()
        row = 0
        col = 0
        
        sheet.write(row, col, "Fecha")
        sheet.write(row, col + 1, "Serie")
        sheet.write(row, col + 2, "Numero")
        sheet.write(row, col + 3, "Tipo de Doc.")
        sheet.write(row, col + 4, "RUC/DNI")
        sheet.write(row, col + 5, "Cliente")
        sheet.write(row, col + 6, "Moneda")
        sheet.write(row, col + 7, "Op. Gravada")
        sheet.write(row, col + 8, "Op. Exonerada")
        sheet.write(row, col + 9, "Op. Inafecta")
        
        sheet.write(row, col + 10, "ICBPER")
        sheet.write(row, col + 11, "ICBPER Cantidad")
        
        sheet.write(row, col + 12, "Impuesto")
        sheet.write(row, col + 13, "Total")
        sheet.write(row, col + 14, "Fecha")
        sheet.write(row, col + 15, "Tipo")
        sheet.write(row, col + 16, "Ser. Ref.")
        sheet.write(row, col + 17, "Num. Ref.")
        sheet.write(row, col + 18, "Cod. Ret.")
        
        row += 1
        report_id = self.env['pe.invoice.report.wizard'].browse(objs.ids)
        data = report_id._prepare_sale_report()
        
        invoices = data.get('invoice_ids', [])
        invoice_ids = self.env['account.move'].search([('id','in',invoices)], order = "invoice_date asc")
        
        for invoice_id in invoice_ids:
            vals = self._op_total(invoice_id)
            sheet.write(row, col, invoice_id.invoice_date or "", date)
            sheet.write(row, col+1, invoice_id.l10n_latam_document_number and invoice_id.l10n_latam_document_number[:4] or "")
            sheet.write(row, col+2, invoice_id.l10n_latam_document_number and invoice_id.l10n_latam_document_number[5:] or "")
            sheet.write(row, col+3, invoice_id.pe_invoice_code or "")
            sheet.write(row, col+4, invoice_id.partner_id.pe_doc_number or "")
            if invoice_id.pe_annul:
                sheet.write(row, col+5, "Anulado")
            else:
                sheet.write(row, col+5, invoice_id.partner_id.name or "")
            if invoice_id.pe_annul:
                row += 1
                continue
            sheet.write(row, col+6, invoice_id.currency_id.name or "")
            sheet.write(row, col+7, vals['op_gravada'] or 0.0, digit2)
            sheet.write(row, col+8, vals['op_exonerada'] or 0.0, digit2)
            sheet.write(row, col+9, vals['op_inafecta'] or 0.0, digit2)
            
            sheet.write(row, col+10, vals['op_icbper'] or 0.0, digit2)
            sheet.write(row, col+11, vals['op_icbper_amount'] or 0.0, digit2)
            
            sheet.write(row, col+12, vals['igv_amount'] or 0.0, digit2)
            sheet.write(row, col+13, invoice_id.amount_total or 0.0, digit2)
            sheet.write(row, col+14, invoice_id.reversed_entry_id.invoice_date or "", date)
            sheet.write(row, col+15, invoice_id.reversed_entry_id.pe_invoice_code or "")
            sheet.write(row, col+16, invoice_id.reversed_entry_id.name and invoice_id.reversed_entry_id.l10n_latam_document_number.split("-")[0] or "")
            sheet.write(row, col + 17, invoice_id.reversed_entry_id.name and invoice_id.reversed_entry_id.l10n_latam_document_number.split("-")[-1] or "")
            sheet.write(row, col + 18, invoice_id.pe_return_code or "")
            row += 1

    