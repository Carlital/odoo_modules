# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportKardex(models.Model):
    _name = "report.kardex"

    user_id = fields.Many2one(
        string="Usuario",
        comodel_name="res.users",
    )

    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
    )

    kardex_per_company_ids = fields.One2many(
        string="Kardex Per Company",
        comodel_name="kardex.per.company",
        inverse_name="report_kardex_id",
    )
    has_countries = fields.Boolean(
        string="Has Countries",
    )
    has_brands = fields.Boolean(
        string="Has Brands",
    )
    has_categories = fields.Boolean(
        string="Has Categories",
    )

    def _get_companies(self):
        company_ids = self.kardex_per_company_ids.mapped("company_id")
        companies = {}
        for x in company_ids:
            companies.update(
                {
                    x.id: {
                        "name": x.nickname,
                        "tam": len(
                            self.env["stock.location"].search(
                                [
                                    ("company_id", "=", x.id),
                                    ("usage", "in", ["internal"]),
                                ]
                            )
                        ),
                    }
                }
            )
        return companies

    def _get_location_by_company_order(self):
        companies = self._get_companies()
        locations = {}
        for company in companies:
            location_ids = self.env["stock.location"].search(
                [("company_id", "=", company), ("usage", "in", ["internal"])]
            )
            for location in location_ids:

                locations.update({location.id: location.display_name})

        return locations

    def _get_products_order_dict(self):
        products = (
            self.env["kardex.per.company"]
            .search([("report_kardex_id", "=", self.id)])
            .mapped("product_id")
            .ids
        )
        products_dict = {}
        for product in products:
            product_id = self.env["product.product"].browse(product)
            if not products_dict.get(product):
                products_dict[product] = {
                    "internal_note": product_id.default_code,
                    "product_name": product_id.name,
                    "variant_name": self.variant_name(
                        product_id.product_template_attribute_value_ids
                    )
                    or "",
                    "brand": product_id.product_brand_id.name,
                    "category": product_id.categ_id.name,
                    "barcode": product_id.barcode,
                    "paises": ",".join(product_id.origin_country_ids.mapped("name")),
                    "valores": [],
                    "supplier": self.get_supplier_info(
                        product_id, product_id.company_id
                    ),
                }
        # agrupar por proveedor alfabeticamente
        products_dict = dict(
            sorted(products_dict.items(), key=lambda item: item[1].get("supplier"))
        )
        # INICIAR enumeracion diferente por CADA supplier diferente al diccionario

        # 3939: {'internal_note': False, 'product_name': 'TUTSI POP 20 Gr', 'variant_name': '', 'brand': 'mi marca 1', 'category': 'All', 'barcode': '7501063501334', 'paises': 'Perú', 'valores': [], 'supplier': '', 'supplier_num': 1}
        # 3656: {'internal_note': False, 'product_name': 'BLACKBERRY JAM / MERMELADA MORA 200 Gr', 'variant_name': '', 'brand': 'La Chilenita', 'category': 'All', 'barcode': '7702097036643', 'paises': 'Perú', 'valores': [], 'supplier': ' ALIMENTOS POLAR EUROPA, SL', 'supplier_num': 1}
        # 3992: {'internal_note': False, 'product_name': 'CORN TORTILLA / TORTILLA MAIZ 500 GR', 'variant_name': '4.5 In Taquera ', 'brand': 'mi marca tort', 'category': 'JUICES', 'barcode': False, 'paises': 'Perú', 'valores': [], 'supplier': 'Intermex Pro General Trading LLC', 'supplier_num': 1}
        # 3993: {'internal_note': False, 'product_name': 'CORN TORTILLA / TORTILLA MAIZ 500 GR', 'variant_name': '6 in Standard ', 'brand': 'mi marca tort', 'category': 'JUICES', 'barcode': False, 'paises': 'Perú', 'valores': [], 'supplier': 'Intermex Pro General Trading LLC', 'supplier_num': 2}

        supplier_num = 1
        supplier = ""
        for product_id in products_dict:
            if products_dict.get(product_id).get("supplier") != supplier:
                supplier_num = 1
                supplier = products_dict.get(product_id).get("supplier")
            products_dict.get(product_id).update({"supplier_num": supplier_num})
            supplier_num += 1

        return products_dict

    def _fill_products_quant(self):
        products_dict = self._get_products_order_dict()
        location_ids = self._get_location_by_company_order()
        for product_id in products_dict:
            for location in location_ids:
                kardex = self.env["kardex.per.company"].search(
                    [
                        ("report_kardex_id", "=", self.id),
                        ("location_id", "=", location),
                        ("product_id", "=", product_id),
                    ]
                )
                if not kardex:
                    products_dict.get(product_id).get("valores").append(0)
                else:
                    products_dict.get(product_id).get("valores").append(kardex.qty)

        return products_dict

    def _get_location_by_company(self):
        location_ids = self.kardex_per_company_ids.mapped("location_id")
        locations = {}
        for x in location_ids:
            if x.company_id.id in location:
                locations.update(
                    {x.company_id: locations.get(x.company_id).append(x.id)}
                )
            else:
                locations.update({x.company_id: [x.id]})
        return locations

    def variant_name(self, attribute_value_ids):
        name = ""
        if attribute_value_ids:
            for attribute_value in attribute_value_ids:
                name += attribute_value.name + " "
        return name

    def get_supplier_info(self, product_id, company_id):
        # si el producto tiene supplier_info se retorna el primero
        supplier_info = self.env["product.supplierinfo"].search(
            [
                ("product_tmpl_id", "=", product_id.product_tmpl_id.id),
                ("sequence", "=", 1),
                ("company_id", "=", 1),
            ]
        )

        if supplier_info:
            return supplier_info.partner_id.name
        return "Sin Proveedor"


class KardexPerCompany(models.Model):
    _name = "kardex.per.company"

    report_kardex_id = fields.Many2one(
        string="Kardex Per Company",
        comodel_name="report.kardex",
        ondelete="restrict",
    )

    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )

    company_id = fields.Many2one(
        string="company",
        comodel_name="res.company",
        ondelete="restrict",
    )

    location_id = fields.Many2one(
        string="location",
        comodel_name="stock.location",
        ondelete="restrict",
    )

    qty = fields.Float(
        string="Qty",
    )
