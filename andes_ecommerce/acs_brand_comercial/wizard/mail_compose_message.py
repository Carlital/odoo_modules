
import base64

from odoo import api, models


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)

        active_model = self._context.get('active_model', False)
        active_id = self._context.get('active_id', False)

        if active_model == 'account.move' and active_id:
            account = self.env[active_model].browse(active_id)
            if account.custom_template_mail_invoice_id:
                result.update({
                    'template_id': account.custom_template_mail_invoice_id.id})

        if active_model == 'sale.order' and active_id:
            order = self.env[active_model].browse(active_id)
            if order.custom_template_mail_sale_id:
                result.update({
                    'template_id': order.custom_template_mail_sale_id.id})

        return result

    def onchange_template_id(
            self, template_id, composition_mode, model, res_id):
        res = super().onchange_template_id(
            template_id, composition_mode, model, res_id)
        context = self.env.context
        active_model = context.get('active_model', False)
        active_id = context.get('active_id', False)
        if active_model and active_model == 'account.move':
            pdf = self.env.ref(
                'acs_brand_comercial.account_invoice_contract').sudo().render_qweb_pdf([active_id])[0]
            attachment = self.env['ir.attachment'].create({
                'name': "Contrato.pdf",
                'type': 'binary',
                'res_id': active_id,
                'res_model': 'account.move',
                'datas': base64.b64encode(pdf),
                'mimetype': 'application/x-pdf',
                'datas_fname': 'Contrato.pdf'
            })
            attachment_ids = res.get(
                'value', {}).get('attachment_ids', [])
            if not attachment_ids:
                attachment_ids = [(6, 0, [attachment.id])]
            else:
                report_ids = attachment_ids[0][-1]
                attachment_ids = report_ids + [attachment.id]
                res.get('value').update(
                    {'attachment_ids': [(6, 0, attachment_ids)]})
        return res
