import json
from odoo.http import request, route
from odoo.addons.website_sale.controllers import main
from odoo.addons.http_routing.models.ir_http import slug
from odoo import fields, http, SUPERUSER_ID, tools, _


class WebsiteSale(main.WebsiteSale):

    @route(
        "/shop/cart/update_option",
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        multilang=False,
    )
    def cart_options_update_json(self, product_and_options, lang=None, **kwargs):
        if lang:
            request.website = request.website.with_context(lang=lang)

        order = request.website.sale_get_order(force_create=True)
        if order.state != "draft":
            request.session["sale_order_id"] = None
            order = request.website.sale_get_order(force_create=True)

        product_and_options = json.loads(product_and_options)
        if product_and_options:
            # The main product is the first, optional products are the rest
            main_product = product_and_options[0]
            values = order._cart_update(
                product_id=main_product["product_id"],
                add_qty=main_product["quantity"],
                product_custom_attribute_values=main_product[
                    "product_custom_attribute_values"
                ],
                no_variant_attribute_values=main_product["no_variant_attribute_values"],
                **kwargs
            )

            line_ids = [values["line_id"]]

            if values["line_id"]:
                # Link option with its parent iff line has been created.
                option_parent = {main_product["unique_id"]: values["line_id"]}
                for option in product_and_options[1:]:
                    parent_unique_id = option["parent_unique_id"]
                    option_values = order._cart_update(
                        product_id=option["product_id"],
                        set_qty=option["quantity"],
                        linked_line_id=option_parent[parent_unique_id],
                        product_custom_attribute_values=option[
                            "product_custom_attribute_values"
                        ],
                        no_variant_attribute_values=option[
                            "no_variant_attribute_values"
                        ],
                        **kwargs
                    )
                    option_parent[option["unique_id"]] = option_values["line_id"]
                    line_ids.append(option_values["line_id"])

            values["notification_info"] = self._get_cart_notification_information(
                order, line_ids
            )
            if product_and_options[0]["custom_price"]:
                cst_price = float(product_and_options[0]["custom_price"])

                order_line = request.env["sale.order.line"].browse(values["line_id"])
                order_line.write({"price_unit": cst_price})
                # refresca la sale_order de la session web
                request.website.sale_get_order(force_create=True)

        values["cart_quantity"] = order.cart_quantity
        request.session["website_sale_cart_quantity"] = order.cart_quantity
        # update session cart with the new values from sale order
        request.session["sale_order_id"] = order.id

        return values

    @http.route(
        ["/shop/confirm_order"], type="http", auth="public", website=True, sitemap=False
    )
    def confirm_order(self, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order) or self.checkout_check_address(
            order
        )
        if redirection:
            return redirection

        order.order_line._compute_tax_id()
        request.session["sale_last_order_id"] = order.id
        request.website.sale_get_order(update_pricelist=False)
        extra_step = request.website.viewref("website_sale.extra_info")
        if extra_step.active:
            return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment")
