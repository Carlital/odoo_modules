# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _acs_get_local_day_utc_range(self):
        tz_name = self.env.user.tz or "UTC"
        try:
            local_tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            local_tz = pytz.UTC

        local_today = datetime.now(pytz.UTC).astimezone(local_tz).date()
        local_start = local_tz.localize(datetime.combine(local_today, time.min))
        local_end = local_start + timedelta(days=1)

        return (
            local_start.astimezone(pytz.UTC).replace(tzinfo=None),
            local_end.astimezone(pytz.UTC).replace(tzinfo=None),
        )

    @api.model
    def _cron_update_daily_top_sellers_pos_category(self):
        """Add top sold products of the current day to a configured POS category."""
        params = self.env["ir.config_parameter"].sudo()

        category_id = int(params.get_param("acs_advanced_search_pos_ondemand.top_category_id", "0") or 0)
        top_limit = int(params.get_param("acs_advanced_search_pos_ondemand.top_limit", "5") or 5)
        min_qty = float(params.get_param("acs_advanced_search_pos_ondemand.min_qty", "100") or 100)

        if not category_id or top_limit <= 0:
            return

        target_category = self.env["pos.category"].sudo().browse(category_id).exists()
        if not target_category:
            return

        start_dt, end_dt = self._acs_get_local_day_utc_range()

        lines_data = self.read_group(
            domain=[
                ("order_id.state", "in", ["paid", "done", "invoiced"]),
                ("order_id.date_order", ">=", fields.Datetime.to_string(start_dt)),
                ("order_id.date_order", "<", fields.Datetime.to_string(end_dt)),
                ("qty", ">", 0),
            ],
            fields=["product_id", "qty:sum"],
            groupby=["product_id"],
            orderby="qty desc",
            limit=top_limit,
            lazy=False,
        )

        product_ids = [
            item["product_id"][0]
            for item in lines_data
            if item.get("product_id") and float(item.get("qty", 0.0)) >= min_qty
        ]
        if not product_ids:
            return

        templates = self.env["product.product"].sudo().browse(product_ids).mapped("product_tmpl_id")
        templates.write({"pos_categ_ids": [(4, target_category.id)]})
