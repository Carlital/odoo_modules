# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PeCPEForm(models.TransientModel):
    _name = "pe.query.cpe.form"
    _description = "From CPE Query"
    _website_form_access = True

    vat = fields.Char("Vat")
    number = fields.Char("Number")
    invoice_date = fields.Date("Date Invoice")
    amount = fields.Float("Amount", digits=(12, 2))
    invoice_id = fields.Many2one('account.move', "Move", compute="_compute_invoice_id")
    document_type_code = fields.Selection(selection=[
        ('01', 'Factura'),
        ('03', 'Boleta'),
        ('07', 'Nota de Crédito'),
        ('08', 'Nota de Débito'), ], string="Document Type Code")

    # @api.model
    # def get_document(self, vals):
    #     vat = vals.get('vat') or False
    #     number = vals.get('number') or False
    #     amount_total = float(vals.get('amount', 0.0))
    #     invoice_date = vals.get('invoice_date') or False
    #     if vat:
    #         invoice_id = self.env['account.move'].sudo().search([('partner_id.vat','=',vat),('name','=',number),('amount_total','=',amount_total),
    #                                                       ('invoice_date','=',invoice_date),('move_type','in',['out_invoice','out_refund']),('pe_annul','=',False)], limit=1)
    #     else:
    #         invoice_id = self.env['account.move'].sudo().search([('name','=',number),('amount_total','=',amount_total),
    #                                                       ('invoice_date','=',invoice_date),('move_type','in',['out_invoice','out_refund']),('pe_annul','=',False)], limit=1)
    #     return invoice_id

    def _get_sql_query(self):
        """ Returns the SQL query to fetch the invoices based on the provided criteria. """

        action_query = """
                       SELECT account_move.id \
                       FROM account_move \
                                INNER JOIN res_partner \
                                           ON account_move.partner_id = res_partner.id \
                                INNER JOIN l10n_latam_document_type \
                                           ON account_move.l10n_latam_document_type_id = l10n_latam_document_type.id
                       WHERE account_move.move_type IN ('out_invoice', 'out_refund')
                         AND (account_move.name ~ %s OR account_move.name ~ %s)
                         AND account_move.invoice_date = %s
                         AND account_move.amount_total = %s
                       """
        if self.vat:
            action_query += " AND res_partner.vat = %s"
        if self.document_type_code:
            action_query += " AND l10n_latam_document_type.code = %s"
        action_query += " ORDER BY l10n_latam_document_type.code DESC, account_move.write_date DESC LIMIT 1"
        return action_query

    def _compute_invoice_id(self):
        for record in self:
            if not record.vat and not record.number:
                record.invoice_id = False
                continue
            query = record._get_sql_query()
            # Prepare the parameters for the SQL query
            if record.number and record.invoice_date and record.amount:
                try:
                    number = "%s %s-0{0,8}%d" % (record.number.split('-')[0][0], record.number.split('-')[0],
                                                 int(record.number.split('-')[1]))
                    number1 = "%s %s-0{0,8}%d" % (record.number.split('-')[0][0], record.number.split('-')[0][1:],
                                                  int(record.number.split('-')[1]))
                    params = [
                        number,
                        number1,
                        record.invoice_date,
                        record.amount,
                    ]
                    if record.vat:
                        params.append(record.vat)
                    if record.document_type_code:
                        params.append(record.document_type_code)
                    self.env.cr.execute(query, params)
                    result = self.env.cr.fetchone()
                    if result:
                        invoice_id = result
                        if invoice_id:
                            record.invoice_id = self.env['account.move'].browse(invoice_id)
                        else:
                            record.invoice_id = False
                    else:
                        record.invoice_id = False
                except Exception as e:
                    record.invoice_id = False
            else:
                record.invoice_id = False