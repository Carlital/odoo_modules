# -*- coding: utf-8 -*-
{
    "name": "POS Product Sort Priority",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Sort products in POS by custom priority",
    "description": """
        Add custom sorting priority for products in Point of Sale.
        Products with higher priority numbers appear first.
        If priority is the same, products are sorted alphabetically.
        Compatible with Odoo 11 order_sequence field logic.
    """,
    "author": "ACS",
    "website": "https://www.acsystemas.com",
    "depends": ["point_of_sale", "product"],
    "data": [
        "views/product_template_view.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "acs_pos_sort_products/static/src/js/product_screen.js",
            "acs_pos_sort_products/static/src/xml/receipt_screen.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
