from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """
        Override search_read to handle custom search logic for product.template.
        """
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
            domain = new_domain

        return super().search_read(domain, fields=fields, offset=offset, limit=limit, order=order)