# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockProductKardex(models.TransientModel):
    _name = "product.kardex"
    _description = "Stock Kardex"

    product_brand_ids = fields.Many2many(
        string="Marcas",
        comodel_name="product.brand",
    )
    product_category_ids = fields.Many2many(
        string="Categorias",
        comodel_name="product.category",
    )

    def _create_default_company_ids(self):
        return self.env.companies.ids

    company_ids = fields.Many2many(
        string="Compañias",
        comodel_name="res.company",
        column1="company_id",
        column2="kardex_id",
        default=_create_default_company_ids,
    )
    country_ids = fields.Many2many(
        string="Paises",
        comodel_name="res.country",
        column1="country_id",
        column2="kardex_id",
    )

    filter_by_country = fields.Boolean(
        string="Filtrar por país",
    )
    filter_by_brand = fields.Boolean(
        string="Filtrar por marca",
    )
    filter_by_category = fields.Boolean(
        string="Filtrar por categoria",
    )

    def generar(self):

        self.env["kardex.per.company"].search([]).unlink()
        self.env["report.kardex"].search([]).unlink()
        location_ids = self.env["stock.location"].search(
            [("company_id", "in", self.company_ids.ids), ("usage", "in", ["internal"])]
        )
        kardex_id = self.env["report.kardex"].create({"user_id": self.env.user.id})
        country_ids = self.country_ids.ids
        brand_ids = self.product_brand_ids.ids
        category_ids = self.product_category_ids.ids

        if country_ids or brand_ids or category_ids:

            product_ids = self.env["product.product"].search([])

            if country_ids:
                product_ids = product_ids.filtered(
                    lambda x: x.origin_country_ids.id in country_ids
                )

            if brand_ids:
                product_ids = product_ids.filtered(
                    lambda x: x.product_brand_id.id in brand_ids
                )

            if category_ids:
                product_ids = product_ids.filtered(
                    lambda x: x.categ_id.id in category_ids
                )

        else:
            product_ids = self.env["product.product"].search([])
        product_ids = product_ids.ids

        for r in location_ids:
            if product_ids:
                stock_quants = self.env["stock.quant"].search(
                    [("location_id", "=", r.id), ("product_id", "in", product_ids)]
                )
            # else:
            #     stock_quants = self.env["stock.quant"].search(
            #         [("location_id", "=", r.id)]
            #     )
            else:
                stock_quants = self.env["stock.quant"]

            for quant in stock_quants:
                current_line_id = self.env["kardex.per.company"].search(
                    [
                        ("report_kardex_id", "=", kardex_id.id),
                        ("product_id", "=", quant.product_id.id),
                        ("location_id", "=", r.id),
                    ]
                )
                if current_line_id:
                    current_line_id.write({"qty": quant.quantity})
                else:
                    self.env["kardex.per.company"].create(
                        {
                            "product_id": quant.product_id.id,
                            "report_kardex_id": kardex_id.id,
                            "company_id": r.company_id.id,
                            "location_id": r.id,
                            "qty": quant.quantity,
                        }
                    )

        kardex_id.write({"has_countries": True if self.filter_by_country else False})
        kardex_id.write({"has_brands": True if self.filter_by_brand else False})
        kardex_id.write({"has_categories": True if self.filter_by_category else False})

        return self.env.ref(
            "acs_stock_by_companies.action_report_stock_by_company"
        ).report_action(kardex_id)
