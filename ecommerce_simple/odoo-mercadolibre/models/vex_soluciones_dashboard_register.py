from odoo import models, fields, api
import json
from datetime import datetime, time, timedelta
from pytz import timezone, UTC
import logging
_logger = logging.getLogger(__name__)
class VexDashboardRecord(models.Model):
    _name = "vex.dashboard.record"
    _description = "Vex Dashboard Record"
    _order = "date desc"

    date = fields.Date("Fecha", default=fields.Date.context_today, required=True)

    orders_synced_today = fields.Integer()
    total_orders = fields.Integer()
    new_customers_this_month = fields.Integer()
    total_customers = fields.Integer()
    total_products = fields.Integer()
    total_questions = fields.Integer()

    top_clients_json = fields.Text()
    top_products_json = fields.Text()
    recent_orders_json = fields.Text()
    customers_evolution_json = fields.Text()
    total_earnings_json = fields.Text()
    average_customer_order_json = fields.Text()
    top_categories_json = fields.Text()
    completed_and_canceled_json = fields.Text()
    sales_by_channel_json = fields.Text()
    questions_by_category_json = fields.Text()
    
    instance_id = fields.Many2one('vex.instance', string='Instance', readonly=True)

    @api.model
    def generate_json_dashboard(self, *args, **kwargs):
        record = self.search([('instance_id','=',self.env.user.meli_instance_id.id)], order="date desc", limit=1)
        if not record:
            return {}        
        return {
            "orders_synced_today": record.orders_synced_today,
            "total_orders": record.total_orders,
            "new_customers_last_month": record.new_customers_this_month,
            "total_customers": record.total_customers,
            "total_products": record.total_products,
            "total_questions": record.total_questions,
            "top_clients": json.loads(record.top_clients_json or "[]"),
            "top_products": json.loads(record.top_products_json or "[]"),
            "recent_orders": json.loads(record.recent_orders_json or "[]"),
            "customers_evolution": json.loads(record.customers_evolution_json or "{}"),
            "total_earnings": json.loads(record.total_earnings_json or "{}"),
            "average_customer_order": json.loads(record.average_customer_order_json or "{}"),
            "top_categories_sold": json.loads(record.top_categories_json or "[]"),
            "completed_and_canceled": json.loads(record.completed_and_canceled_json or "{}"),
            "sales_distribution_by_channel": json.loads(record.sales_by_channel_json or "{}"),
            "questions": json.loads(record.questions_by_category_json or "{}")
        }

    @api.model
    def generate_dashboard_record_daily(self):
        user_tz = self.env.user.tz or 'UTC'
        today = datetime.now(timezone(user_tz)).date()
        
        # Si no se pasa instance_id explícitamente, usar el del usuario actual
        if self.env.user.meli_instance_id:
            instances = self.env['vex.instance'].browse([self.env.user.meli_instance_id.id])
        else:
            instances = self.env['vex.instance'].search([('store_type', '=', 'mercadolibre')])

        for instance in instances:
            _logger.info(f"Generando dashboard para {today} - Instancia: {instance.name}")
            
            mercado_libre_marketplace = self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre')
            existing_record = self.search([
                ('date', '=', today),
                ('instance_id', '=', instance.id)
            ], limit=1)

            primer_dia_mes = today.replace(day=1)
            values = {
                'date': today,
                'instance_id': instance.id,
                'orders_synced_today': self.env['sale.order'].search_count([
                    ('meli_date_create_without_time', '=', today),
                    ('meli_order_id', '!=', ''),
                    ('instance_id', '=', instance.id)
                ]),
                'total_orders': self.env['sale.order'].search_count([
                    ('marketplace_ids', 'in', [mercado_libre_marketplace.id]),
                    ('instance_id', '=', instance.id)
                ]),
                'new_customers_this_month': self.env['res.partner'].search_count([
                    ('create_date', '>=', primer_dia_mes),
                    ('marketplace_ids', 'in', [mercado_libre_marketplace.id]),
                    ('instance_id', '=', instance.id)
                ]),
                'total_customers': self.env['res.partner'].search_count([
                    ('marketplace_ids', 'in', [mercado_libre_marketplace.id]),
                    ('instance_id', '=', instance.id)
                ]),
                'total_products': self.env['product.template'].search_count([
                    ('marketplace_ids', 'in', [mercado_libre_marketplace.id]),
                    ('meli_status', '=', 'active'),
                    ('instance_id', '=', instance.id)
                ]),
                'total_questions': self.env['vex.meli.questions'].search_count([
                    ('meli_instance_id', '=', instance.id)
                ]),

                'top_clients_json': json.dumps(self._get_top_clients(instance)),
                'top_products_json': json.dumps(self._get_top_products(instance)),
                'recent_orders_json': json.dumps(self._get_recent_orders(instance)),
                'customers_evolution_json': json.dumps(self._get_customers_evolution(instance)),
                'total_earnings_json': json.dumps(self._get_total_earnings(instance)),
                'average_customer_order_json': json.dumps(self._get_avg_order(instance)),
                'top_categories_json': json.dumps(self._get_top_categories(instance)),
                'completed_and_canceled_json': json.dumps(self._get_completed_and_canceled(instance)),
                'sales_by_channel_json': json.dumps(self._get_sales_by_channel(instance)),
                'questions_by_category_json': json.dumps(self._get_questions_by_category(instance)),
            }

            if existing_record:
                existing_record.write(values)
            else:
                self.create(values)

    def _get_top_clients(self, instance):
        query = """
            SELECT MIN(s.id) as sale_id, s.partner_id, COUNT(*) as order_count, SUM(s.amount_total) as total_volume
            FROM sale_order s
            WHERE s.state IN ('sale', 'done')
            AND s.instance_id = %s
            GROUP BY s.partner_id
            ORDER BY total_volume DESC
            LIMIT 10
        """
        self.env.cr.execute(query, (instance.id,))
        return [{
            'name': self.env['res.partner'].browse(r[1]).name,
            'order_number': r[2],
            'volume': r[3],
            'sale_order_id': r[0],
        } for r in self.env.cr.fetchall()]


    def _get_top_products(self, instance):
        query = """
            SELECT MIN(l.id) as line_id, l.product_id, COUNT(*) as qty, SUM(l.price_total) as total
            FROM sale_order_line l
            JOIN sale_order s ON l.order_id = s.id
            WHERE s.instance_id = %s AND s.state IN ('sale', 'done')
            GROUP BY l.product_id
            ORDER BY qty DESC
            LIMIT 10
        """
        self.env.cr.execute(query, (instance.id,))
        return [{
            'product_name': self.env['product.product'].browse(r[1]).name,
            'number_of_sales': r[2],
            'sales_volume': r[3],
            'id': r[0]
        } for r in self.env.cr.fetchall()]

    def _get_recent_orders(self, instance):
        orders = self.env['sale.order'].search([
            ('meli_order_id', '!=', ''),
            ('instance_id', '=', instance.id)
        ], order="date_order desc", limit=5)

        return [{
            'id': o.id,
            'name': o.partner_id.name,
            'order_number': o.name,
            'mail': o.partner_id.email or "",
            'phone': o.partner_id.phone or "",
            'amount': o.amount_total,
            'products': len(o.order_line)
        } for o in orders]

    def _get_customers_evolution(self, instance):
        labels, data = [], []
        for i in range(6):
            date = fields.Date.today() - timedelta(days=i * 30)
            first_day = date.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1)

            labels.insert(0, first_day.strftime("%b"))
            count = self.env['res.partner'].search_count([
                ('customer_rank', '>', 0),
                ('create_date', '>=', first_day),
                ('create_date', '<', last_day),
                ('instance_id', '=', instance.id),
            ])
            data.insert(0, count)

        return {
            "labels": labels,
            "datasets": [{
                "label": "Customers",
                "data": data
            }]
        }

    def _get_total_earnings(self, instance):
        labels, data = [], []
        for i in range(6):
            date = fields.Date.today() - timedelta(days=i * 30)
            first_day = date.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1)

            orders = self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('instance_id', '=', instance.id),
                ('date_order', '>=', first_day),
                ('date_order', '<', last_day)
            ])

            labels.insert(0, first_day.strftime("%b"))
            data.insert(0, sum(orders.mapped('amount_total')))

        return {
            "labels": labels,
            "datasets": [{
                "label": "Earnings",
                "data": data
            }]
        }

    def _get_avg_order(self, instance):
        labels, data = [], []
        for i in range(6):
            date = fields.Date.today() - timedelta(days=i * 30)
            first_day = date.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1)

            orders = self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('instance_id', '=', instance.id),
                ('date_order', '>=', first_day),
                ('date_order', '<', last_day)
            ])

            avg = sum(orders.mapped('amount_total')) / len(orders) if orders else 0
            labels.insert(0, first_day.strftime("%b"))
            data.insert(0, avg)

        return {
            "labels": labels,
            "datasets": [{
                "label": "Sales evolution",
                "data": data
            }]
        }

    def _get_top_categories(self, instance):
        query = """
            SELECT pt.categ_id, SUM(sol.price_total) AS total_sales
            FROM sale_order_line sol
            JOIN product_product pp ON sol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN sale_order so ON sol.order_id = so.id
            WHERE so.state IN ('sale', 'done')
            AND so.instance_id = %s
            GROUP BY pt.categ_id
            ORDER BY total_sales DESC
            LIMIT 5
        """
        self.env.cr.execute(query, (instance.id,))
        result = []
        for categ_id, total in self.env.cr.fetchall():
            category = self.env['product.category'].browse(categ_id)
            result.append({
                "category": category.display_name,
                "sales": total
            })
        return result


    def _get_completed_and_canceled(self, instance):
        labels, completed, canceled = [], [], []
        for i in range(5):
            date = fields.Date.today() - timedelta(days=i * 30)
            first_day = date.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1)

            labels.insert(0, first_day.strftime("%b"))

            completed_count = self.env['sale.order'].search_count([
                ('state', '=', 'done'),
                ('instance_id', '=', instance.id),
                ('date_order', '>=', first_day),
                ('date_order', '<', last_day),
            ])
            canceled_count = self.env['sale.order'].search_count([
                ('state', '=', 'cancel'),
                ('instance_id', '=', instance.id),
                ('date_order', '>=', first_day),
                ('date_order', '<', last_day),
            ])

            completed.append(completed_count)
            canceled.append(canceled_count)

        return {
            "labels": labels,
            "datasets": [
                {"label": "Completed", "data": completed},
                {"label": "Canceled", "data": canceled}
            ]
        }

    def _get_sales_by_channel(self, instance):
        labels = []
        channel_totals = {}

        for i in range(5):
            date = fields.Date.today() - timedelta(days=i * 30)
            first_day = date.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1)
            month_label = first_day.strftime("%b")
            labels.insert(0, month_label)

            orders = self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('instance_id', '=', instance.id),
                ('date_order', '>=', first_day),
                ('date_order', '<', last_day),
            ])

            for order in orders:
                channel = order.meli_context_channel or 'Desconocido'
                if channel not in channel_totals:
                    channel_totals[channel] = [0] * 5
                channel_totals[channel][-(i + 1)] += order.amount_total

        datasets = [{"label": channel, "data": totals} for channel, totals in channel_totals.items()]

        return {
            "labels": labels,
            "datasets": datasets
        }

    def _get_questions_by_category(self, instance):
        questions = self.env['vex.meli.questions'].search([
            ('meli_instance_id', '=', instance.id),
            ('meli_item_id', '!=', False),
        ])

        category_counts = {}

        product_tmpl_model = self.env['product.template']
        for question in questions:
            product_tmpl = product_tmpl_model.search([
                ('meli_product_id', '=', question.meli_item_id),
                ('instance_id', '=', instance.id)
            ], limit=1)

            if product_tmpl:
                category = product_tmpl.categ_id
                name = category.display_name if category else "Sin Categoría"
            else:
                name = "Producto no encontrado"

            category_counts[name] = category_counts.get(name, 0) + 1

        return {
            "labels": list(category_counts.keys()),
            "datasets": [{
                "label": "Questions by Category",
                "data": list(category_counts.values())
            }]
        }