# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import os
import time
import unicodedata
import uuid

from PyPDF2 import PdfFileReader, PdfFileWriter
try:
    from PyPDF2.errors import PdfReadError
except ImportError:
    from PyPDF2.utils import PdfReadError
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.rl_config import TTFSearchPath
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from werkzeug.urls import url_join, url_quote
from random import randint
from markupsafe import Markup
from hashlib import sha256
from PIL import UnidentifiedImageError

from odoo import api, fields, models, http, _, Command
from odoo.tools import config, email_normalize, get_lang, is_html_empty, format_date, formataddr, groupby
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class SignRequestItem(models.Model):
    _inherit = "sign.request.item"

    
    def _send_signature_access_mail(self):
        for signer in self:
            #email = self.env['ir.config_parameter'].sudo().get_param('addval_sign_extension.sign_request_mail')
            email = signer.communication_company_id.outgoing_mail
            signer_email_normalized = email_normalize(signer.signer_email or '')
            signer_lang = get_lang(self.env, lang_code=signer.partner_id.lang).code
            context = {'lang': signer_lang}
            body = self.env['ir.qweb']._render('sign.sign_template_mail_request', {
                'record': signer,
                'link': url_join(signer.get_base_url(), "sign/document/mail/%(request_id)s/%(access_token)s" % {'request_id': signer.sign_request_id.id, 'access_token': signer.sudo().access_token}),
                'subject': signer.sign_request_id.subject,
                'body': signer.sign_request_id.message if not is_html_empty(signer.sign_request_id.message) else False,
                'use_sign_terms': self.env['ir.config_parameter'].sudo().get_param('sign.use_sign_terms'),
                'user_signature': signer.create_uid.signature,
            }, lang=signer_lang, minimal_qcontext=True)

            attachment_ids = signer.sign_request_id.attachment_ids.ids
            self.env['sign.request']._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': signer.sign_request_id.reference},
                {'model_description': _('Signature'), 'company': signer.communication_company_id or signer.sign_request_id.create_uid.company_id},
                {'email_from': email,
                 'author_id': signer.create_uid.partner_id.id,
                 'email_to': formataddr((signer.partner_id.name, signer_email_normalized)),
                 'attachment_ids': attachment_ids,
                 'subject': signer.sign_request_id.subject},
                force_send=True,
                lang=signer_lang,
            )
            signer.is_mail_sent = True
            del context
    
    def _send_completed_document_mail(self, signers, request_edited, partner, access_token=None, with_message_cc=True, force_send=False):
        self.ensure_one()
        if access_token is None:
            access_token = self.access_token
        #email = self.env['ir.config_parameter'].sudo().get_param('addval_sign_extension.sign_request_mail')
        email = self.communication_company_id.outgoing_mail
        partner_lang = get_lang(self.env, lang_code=partner.lang).code
        base_url = self.get_base_url()
        body = self.env['ir.qweb']._render('sign.sign_template_mail_completed', {
            'record': self,
            'link': url_join(base_url, 'sign/document/%s/%s' % (self.id, access_token)),
            'subject': '%s signed' % self.reference,
            'body': self.message_cc if with_message_cc and not is_html_empty(self.message_cc) else False,
            'recipient_name': partner.name,
            'recipient_id': partner.id,
            'signers': signers,
            'request_edited': request_edited,
            }, lang=partner_lang, minimal_qcontext=True)

        self.env['sign.request']._message_send_mail(
            body, 'mail.mail_notification_light',
            {'record_name': self.reference},
            {'model_description': 'signature', 'company': self.communication_company_id or self.create_uid.company_id},
            {'email_from': email,
             'author_id': self.create_uid.partner_id.id,
             'email_to': partner.email_formatted,
             'subject': _('%s has been edited and signed', self.reference) if request_edited else _('%s has been signed', self.reference),
             'attachment_ids': self.attachment_ids.ids + self.completed_document_attachment_ids.ids},
            force_send=force_send,
            lang=partner_lang,
        )