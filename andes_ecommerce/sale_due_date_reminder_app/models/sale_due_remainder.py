# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = "Sale Order"

    date_due = fields.Date(string='Due Date')

    def sale_due_remainder_action_email(self):
        sales = self.env['sale.order'].search([('date_due', '!=', False)])
        user_id = self.env['res.users'].browse(self.env.context.get('uid'))
        if sales:
            for order in sales:
                email_to = []
                for follower in order.message_follower_ids:
                    email_to.append(follower.partner_id.id)
                if not isinstance(order.date_due, bool):
                    date_two_days_ago = order.date_due - timedelta(days=2)
                    if order.date_due == datetime.now().date():
                        # template_id = self.env['ir.model.data']._xmlid_to_res_id(
                        #     'sale_due_date_reminder_app.sale_due_remainder_email_template')
                        template_id = self.env.ref('sale_due_date_reminder_app.sale_due_remainder_email_template')
                        template_browse = self.env['mail.template'].browse(template_id.id)
                        due_date = order.date_due
                        # if template_browse:
                        #     values = template_browse.generate_email(order.id,
                        #                                             ['subject', 'body_html', 'email_from', 'email_to',
                        #                                              'partner_to', 'email_cc', 'reply_to',
                        #                                              'scheduled_date'])
                        #     values['subject'] = "Reminder about " + order.name + " due on " + str(due_date)
                        #     values['res_id'] = False
                        #     values['author_id'] = user_id.partner_id.id
                        #     values['recipient_ids'] = [(6, 0, email_to)]
                        #     if not values['email_to'] and not values['email_from']:
                        #         pass
                        #
                        #     msg_id = self.env['mail.mail'].create({
                        #         'body_html': values['body_html'],
                        #         'subject': values['subject'],
                        #         'email_to': order.partner_id.email,
                        #         'auto_delete': True,
                        #         'author_id': values['author_id'],
                        #         'email_from': values['email_from'],
                        #         'references': values['mail_server_id'], })
                        #
                        #     mail_mail_obj = self.env['mail.mail']
                        #     if msg_id:
                        #         mail_mail_obj.sudo().send(msg_id)
                        mail_obj = self.env['mail.mail']
                        email_template = self.env['mail.template'].browse(template_id.id)
                        if template_id:
                            values = email_template._generate_template(self.ids,
                                                                       ['attachment_ids',
                                                                        'body_html',
                                                                        'email_cc',
                                                                        'email_from',
                                                                        'email_to',
                                                                        'mail_server_id',
                                                                        'reply_to',
                                                                        'res_id',
                                                                        'scheduled_date',
                                                                        'subject',
                                                                        ]
                                                                       )
                            # value['subject'] = "Email Verification"

                            for res_id, val in list(values.items()):
                                # mail_mail_obj = self.env['mail.mail']
                                msg_id = mail_obj.sudo().create(
                                    {'subject': " Reminder about " + order.name + " due on " + str(due_date),
                                     'email_from': val['email_from'],
                                     'attachment_ids': val['attachment_ids'],
                                     'email_to': order.partner_id.email,
                                     'email_cc': '',
                                     'reply_to': '',
                                     'scheduled_date': '',
                                     'body_html': val['body_html'],
                                     'auto_delete': False,
                                     # 'model' : val['model'],
                                     'mail_server_id': False,
                                     })
                                if msg_id:
                                    mail_obj.sudo().send(msg_id)

                    elif datetime.now().date() == date_two_days_ago:
                        # template_id = self.env['ir.model.data']._xmlid_to_res_id(
                        #     'sale_due_date_reminder_app.sale_before_due_remainder_email_template')
                        template_id = self.env.ref('sale_due_date_reminder_app.sale_due_remainder_email_template')
                        mail_obj = self.env['mail.mail']
                        email_template = self.env['mail.template'].browse(template_id.id)
                        if template_id:
                            values = email_template._generate_template(self.ids,
                                                                       ['attachment_ids',
                                                                        'body_html',
                                                                        'email_cc',
                                                                        'email_from',
                                                                        'email_to',
                                                                        'mail_server_id',
                                                                        'reply_to',
                                                                        'res_id',
                                                                        'scheduled_date',
                                                                        'subject',
                                                                        ]
                                                                       )
                            # value['subject'] = "Email Verification"

                            for res_id, val in list(values.items()):
                                # mail_mail_obj = self.env['mail.mail']
                                msg_id = mail_obj.sudo().create(
                                    {'subject': " Reminder about " + order.name + " due on " + str(due_date),
                                     'email_from': val['email_from'],
                                     'attachment_ids': val['attachment_ids'],
                                     'email_to': order.partner_id.email,
                                     'email_cc': '',
                                     'reply_to': '',
                                     'scheduled_date': '',
                                     'body_html': val['body_html'],
                                     'auto_delete': False,
                                     # 'model' : val['model'],
                                     'mail_server_id': False,
                                     })
                                if msg_id:
                                    mail_obj.sudo().send(msg_id)
                    else:
                        pass

            return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
