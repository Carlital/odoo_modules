{
    "name": "ACS Custom Price Website",
    "version": "17.0.0.0.0",
    "description": "ACS Custom Price Website",
    "summary": "ACS Custom Price Website",
    "author": "ACS",
    "website": "odoo.com",
    "license": "LGPL-3",
    "category": "Website",
    "depends": [
        "base",
        "website_sale",
        "theme_prime",
        "website_sale_product_configurator",
    ],
    "data": [
        "views/product_views.xml",
        "views/template.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "acs_custom_price_website/static/src/js/website_sale.js",
            "acs_custom_price_website/static/src/js/sale_product_configurator_modal.js",
        ],
    },
}
