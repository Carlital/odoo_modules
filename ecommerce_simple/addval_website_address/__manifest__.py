# -*- coding: utf-8 -*-
{
    "name": "Modificaciones Formulario Direcciones Website",
    "summary": """
        Modificaciones Formulario Direcciones Website (addval_website_address)""",
    "description": """
        Modificaciones Formulario Direcciones Website (addval_website_address)
    """,
    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Website",
    "license": "Other proprietary",
    "version": "0.1",
    "data": [
        "views/website_sale_address.xml",
    ],
    "depends": ["base", "website_sale", "addval_cl_communes"],
    "assets": {
        "web.assets_frontend": [
            "addval_website_address/static/src/js/website_sale.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
