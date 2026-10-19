from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_custom_price = fields.Boolean(string="Precio personalizable?")

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        res = super(ProductTemplate, self)._search_render_results(
            fetch_fields, mapping, icon, limit
        )
        for line in res:
            if line.get("id"):
                product = self.browse(line["id"])
                if product.is_custom_price:
                    line["price"] = "<span>%s</span>" % ("")
                    line["list_price"] = ""
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_custom_price = fields.Boolean(string="Precio personalizable?")
