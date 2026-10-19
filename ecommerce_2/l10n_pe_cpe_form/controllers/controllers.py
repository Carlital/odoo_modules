
import json

from odoo import http, _
from odoo.http import request

from odoo.addons.website.controllers.form import WebsiteForm


class WebsiteForm(WebsiteForm):

    # @http.route('/website/form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    # def website_form(self, model_name, **kwargs):
    #     res = super(WebsiteForm, self).website_form(model_name, **kwargs)
    #     values = {}
    #     if model_name == 'pe.query.cpe.form':
    #         invoice_id =request.env[model_name].get_document(kwargs)
    #         if invoice_id:
    #             url = invoice_id.sudo().get_portal_url()
    #             values['url'] = url
    #             #return request.redirect(url)
    #         #elif invoice_id:
    #         #    values['error_fields'] = _("Document not found")
    #         return values and json.dumps(values) or res
    #     else:
    #         return res

    def _handle_website_form(self, model_name, **kwargs):
        """ Handle the website form submission with ReCaptcha validation """
        res = super(WebsiteForm, self)._handle_website_form(model_name, **kwargs)
        if model_name == 'pe.query.cpe.form':
            values = json.loads(res)
            if values.get('id'):
                query_id = request.env[model_name].browse(values['id'])
                query_id._compute_invoice_id()
                if query_id and query_id.invoice_id:
                    url = query_id.invoice_id.sudo().get_portal_url()
                    values['url'] = url
                    return json.dumps(values)
        return res