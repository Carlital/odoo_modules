from odoo import http
from odoo.http import request

class PrivacyPolicyController(http.Controller):

    @http.route('/web/privacy', type='http', auth='public', website=True)
    def privacy_policy(self, **kwargs):
        policy = request.env['privacy.policy'].sudo().search([], limit=1)
        
        return request.render('privacy_policy.privacy_policy_template', {'policy': policy})
