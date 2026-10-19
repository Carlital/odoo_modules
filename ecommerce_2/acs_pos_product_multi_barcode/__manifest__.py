# /opt/odoo18/custom-addons/acs_pos_product_multi_barcode/__manifest__.py
{
    "name": "POS - Product Multi Barcode",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Integrate product_multi_barcode with Point of Sale",
    "author": "Juan Ayala",
    "license": "AGPL-3",
    "depends": ["product_multi_barcode", "point_of_sale"],
    "assets": {
        "point_of_sale.assets": [
            "acs_pos_product_multi_barcode/static/src/app/store/db.js",
        ],
    },
    "installable": True,
    "auto_install": True,
}
