# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposer, self)._onchange_template_id(template_id, composition_mode, model, res_id)
        def_attachment_ids = self.env.context.get('default_attachment_ids')
        if def_attachment_ids:
            value = res.get('value')
            attachment_ids = value.get('attachment_ids', [])
            attach_ids = []
            if attachment_ids:
                attach_ids = attachment_ids[0][2] + def_attachment_ids[0][2]
            else:
                attach_ids = def_attachment_ids[0][2]
            value['attachment_ids'] = [(6, 0, attach_ids)]
            res['value'] = value
        return res

class AccountInvoiceSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.onchange('template_id')
    def onchange_template_id(self):
        super(AccountInvoiceSend, self).onchange_template_id()

    
    def _send_email(self):
        super(AccountInvoiceSend, self)._send_email()
        if self.is_email:
            self.mapped('invoice_ids').write({'pe_invoice_sent': True})

    @api.model
    def _get_invoice_extra_attachments_data(self, move):
        res = super(AccountInvoiceSend, self)._get_invoice_extra_attachments_data(move)
        if move.pe_is_cpe and move.pe_cpe_id:
            if move.pe_cpe_id.attachment_id:
                res.append(
                {
                    'id': move.pe_cpe_id.attachment_id.id,
                    'name': move.pe_cpe_id.attachment_id.name,
                    'mimetype': move.pe_cpe_id.attachment_id.mimetype,
                    'placeholder': False,
                    'protect_from_deletion': True,
                })
            if move.pe_cpe_id.pe_response_id:
                res.append(
                {
                    'id': move.pe_cpe_id.pe_response_id.id,
                    'name': move.pe_cpe_id.pe_response_id.name,
                    'mimetype': move.pe_cpe_id.pe_response_id.mimetype,
                    'placeholder': False,
                    'protect_from_deletion': True,
                })
        return res