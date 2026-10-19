# -*- coding: utf-8 -*-

import logging

from odoo import api, models
from odoo.osv import expression


_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def acs_pos_ondemand_search_products(self, search_word, limit=20):
        """Search POS products by name, default code and barcode.

        This endpoint is used by the POS frontend when the product is not yet
        loaded in memory.
        """
        query = (search_word or "").strip()
        if not query:
            _logger.debug("[ACS-ONDEMAND] empty query received")
            return []

        limit = max(int(limit or 20), 1)
        _logger.debug("[ACS-ONDEMAND] search start query=%s limit=%s", query, limit)

        exact_domain = [
            ("available_in_pos", "=", True),
            ("default_code", "=", query),
        ]
        exact_products = self.search(exact_domain, limit=limit)
        _logger.debug(
            "[ACS-ONDEMAND] exact matches query=%s count=%s ids=%s",
            query,
            len(exact_products),
            exact_products.ids,
        )

        remaining_limit = max(limit - len(exact_products), 0)
        if not remaining_limit:
            _logger.debug(
                "[ACS-ONDEMAND] done by exact query=%s returned_ids=%s",
                query,
                exact_products.ids,
            )
            return exact_products.ids

        fuzzy_domain = [
            ("available_in_pos", "=", True),
            ("id", "not in", exact_products.ids),
            "|",
            "|",
            ("name", "ilike", query),
            ("default_code", "ilike", query),
            ("barcode", "ilike", query),
        ]
        fuzzy_products = self.search(fuzzy_domain, limit=remaining_limit)
        _logger.debug(
            "[ACS-ONDEMAND] fuzzy matches query=%s count=%s ids=%s",
            query,
            len(fuzzy_products),
            fuzzy_products.ids,
        )

        result_ids = exact_products.ids + fuzzy_products.ids
        remaining_limit = max(limit - len(result_ids), 0)
        if remaining_limit:
            tokens = [token for token in query.split() if token]
            token_domains = [
                expression.OR(
                    [
                        [("name", "ilike", token)],
                        [("default_code", "ilike", token)],
                        [("barcode", "ilike", token)],
                    ]
                )
                for token in tokens
            ]
            token_domain = expression.AND(
                [
                    [("available_in_pos", "=", True)],
                    [("id", "not in", result_ids)],
                    *token_domains,
                ]
            )
            token_products = self.search(token_domain, limit=remaining_limit)
            _logger.debug(
                "[ACS-ONDEMAND] token matches query=%s tokens=%s count=%s ids=%s",
                query,
                tokens,
                len(token_products),
                token_products.ids,
            )
            result_ids += token_products.ids

        _logger.debug("[ACS-ONDEMAND] done query=%s returned_ids=%s", query, result_ids)
        return result_ids
