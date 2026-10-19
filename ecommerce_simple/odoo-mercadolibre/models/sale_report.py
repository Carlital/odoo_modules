from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class SaleReportMonth(models.Model):
    _name = 'sale.report.month'
    _description = 'Ventas Mensuales'

    report_id = fields.Many2one('sale.report', string="Reporte", required=True, ondelete='cascade')
    month = fields.Char(string='Mes')
    sales = fields.Float(string='Ventas Totales')
    date = fields.Date(string='Fecha')  # Si lo estás usando en la vista

    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True)
    #date = fields.Date(string='Fecha')  # Definir el campo 'date' correctamente si es necesario
    total_sales = fields.Float(string='Ventas Totales', compute='_compute_total_sales')
    month_sales = fields.One2many('sale.report.month', 'report_id', string="Ventas por Mes")

class SaleReport(models.Model):
    _name = 'sale.report'
    _description = 'Historial de Ventas Mensual'
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, required=True)
    

    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True)
    total_sales = fields.Float(string='Ventas Totales', compute='_compute_total_sales')
    month_sales = fields.One2many('sale.report.month', 'report_id', string="Ventas por Mes")

    # Asegúrate de definir correctamente el campo 'date'
    date = fields.Date(string='Fecha')  # Agrega el atributo string si necesitas el campo
    
    total_sales = fields.Float(string='Ventas Totales', compute='_compute_total_sales')
    month_sales = fields.One2many('sale.report.month', 'report_id', string="Ventas por Mes")

    @api.depends('date_from', 'date_to')
    def _compute_total_sales(self):
        for record in self:
            orders = self.env['sale.order'].search([
                ('date_order', '>=', record.date_from),
                ('date_order', '<=', record.date_to),
                ('state', 'in', ['sale', 'done'])  # Filtra solo los pedidos confirmados
            ])
            record.total_sales = sum(order.amount_total for order in orders)

    def get_sales_by_month(self):
        """Este método agrupa las ventas mes a mes entre `date_from` y `date_to`."""
        self.ensure_one()  # Para asegurarse de que estamos trabajando con un solo registro
        self.month_sales.unlink()  # Limpiar los registros anteriores de ventas mensuales

        current_date = self.date_from
        while current_date <= self.date_to:
            next_date = current_date + relativedelta(months=1)
            sales_in_month = self.env['sale.order'].search([
                ('date_order', '>=', current_date),
                ('date_order', '<', next_date),
                ('state', 'in', ['sale', 'done'])
            ])
            total_month_sales = sum(order.amount_total for order in sales_in_month)

            # Crear un nuevo registro en el modelo `sale.report.month`
            self.env['sale.report.month'].create({
                'report_id': self.id,
                'month': current_date.strftime('%B %Y'),
                'sales': total_month_sales,
            })

            current_date = next_date

    # FALTA IMPORTAR COMENTADO PARA QUE NO PETE 
    # def export_sales_to_csv(self):
    #     """Generar archivo CSV con el historial de ventas mes a mes."""
    #     # Obtener los datos agrupados por mes
    #     sales_data = self.get_sales_by_month()

    #     # Crear el archivo CSV
    #     file_data = StringIO() 
    #     writer = csv.writer(file_data, delimiter=',')
    #     writer.writerow(['Mes', 'Ventas Totales'])

    #     for row in sales_data:
    #         writer.writerow([row['month'], row['sales']])

    #     # Guardar el archivo CSV como base64 para su descarga
    #     file_data.seek(0)
    #     csv_content = file_data.getvalue()
    #     file_data.close()

    #     # Codificar en base64
    #     self.data_file = base64.b64encode(csv_content.encode('utf-8'))
    #     self.data_filename = f"historial_ventas_{self.date_from}_{self.date_to}.csv"

    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f"/web/content?model=sale.report&id={self.id}&field=data_file&download=true&filename={self.data_filename}",
    #         'target': 'self',
    #     }
