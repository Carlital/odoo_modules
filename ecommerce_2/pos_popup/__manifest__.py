{
    "name": "POS popup",
    "version": "1.0",
    "description": "Agrega un popup al POS al momento de agregar un producto",
    "summary": "Agrega un popup al POS al momento de agregar un producto",
    "author": "ACS",
    "website": "odoo.com",
    "license": "LGPL-3",
    "category": "Point of Sale",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_popup/static/src/js/ProductScreen.js",
        ]
    },
}
