from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class CustomSearchController(http.Controller):

    @http.route('/web/dataset/call_kw/product.template/web_search_read', type='json', auth='user')
    def custom_template_web_search_read(self, model, method, args, kwargs):
        """
        Intercept web_search_read for product.template and modify search logic.
        """
        domain = kwargs.get('domain', [])
        if domain:
            new_domain = []
            for condition in domain:
                if isinstance(condition, (list, tuple)) and condition[1] in ("ilike", "like"):
                    search_term = condition[2]
                    words = search_term.split()
                    if words:
                        modified_term = "%%".join(words)
                        new_condition = (condition[0], condition[1], f"%{modified_term}%")
                        new_domain.append(new_condition)
                    else:
                        new_domain.append(condition)
                else:
                    new_domain.append(condition)
            kwargs['domain'] = new_domain

        kwargs.pop('context', {})

        Model = request.env[model]
        method_to_call = getattr(Model, method)
        return method_to_call(*args, **kwargs)

    @http.route('/web/dataset/call_kw/product.product/web_search_read', type='json', auth='user')
    def custom_product_web_search_read(self, model, method, args, kwargs):
        """
        Intercept web_search_read for product.product and modify search logic.
        """
        
        domain = kwargs.get('domain', [])
        if domain:
            new_domain = []
            for condition in domain:
                if isinstance(condition, (list, tuple)) and condition[1] in ("ilike", "like"):
                    search_term = condition[2]
                    words = search_term.split()
                    if words:
                        modified_term = "%%".join(words)
                        new_condition = (condition[0], condition[1], f"%{modified_term}%")
                        new_domain.append(new_condition)
                    else:
                        new_domain.append(condition)
                else:
                    new_domain.append(condition)
            kwargs['domain'] = new_domain

        kwargs.pop('context', {})

        Model = request.env[model]
        method_to_call = getattr(Model, method)
        return method_to_call(*args, **kwargs)
