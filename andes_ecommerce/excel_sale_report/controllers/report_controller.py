import pandas as pd
import xlsxwriter
from odoo import http
from odoo.http import request
from io import BytesIO
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ReportController(http.Controller):

    @http.route('/report/excel_sale_report/download_excel', type='http', auth="user", csrf=False)
    def download_excel(self, start_date, end_date):
        try:
            # Validación de fechas ingresadas
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

            if start_date > end_date:
                return request.make_response(
                    "La fecha de inicio no puede ser posterior a la fecha de fin.",
                    [('Content-Type', 'text/plain')]
                )

            account_move_lines = request.env['account.move.line'].search([
                ('move_id.state', '=', 'posted'),
                ('move_id.invoice_date', '>=', start_date),
                ('move_id.invoice_date', '<=', end_date),
            ])

            if not account_move_lines:
                return request.make_response(
                    "No se encontraron ventas con facturas en el periodo seleccionado.",
                    [('Content-Type', 'text/plain')]
                )

            current_company = request.env.company
            company_code = current_company.company_registry or 'Sin Código'

            
            product_data = {}
            for line in account_move_lines:
                product = line.product_id
                price_unit = line.price_unit

                if not product.name or product.name.strip() == '' or price_unit == 0.0:
                    continue

                if product not in product_data:
                    product_data[product] = {
                        'product_name': product.name.strip(),
                        'prices': []
                    }
                product_data[product]['prices'].append(price_unit)

            data = {
                "COD. EMPRESA": [],
                "COD. PROD.": [],
                "P. MAX.": [],
                "P. MIN.": [],
                "P. MEDIO": [],
                "DESCRIPCIÓN DEL PRODUCTO": [],
            }

            for product, values in product_data.items():
                prices = values['prices']
                max_price = max(prices)
                min_price = min(prices)
                avg_price = (max_price + min_price) / 2

                data["COD. EMPRESA"].append(company_code)
                data["COD. PROD."].append(product.default_code or 'N/A')
                data["P. MAX."].append(max_price)
                data["P. MIN."].append(min_price)
                data["P. MEDIO"].append(avg_price)
                data["DESCRIPCIÓN DEL PRODUCTO"].append(values['product_name'])

            df = pd.DataFrame(data)

            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet("Reporte de Precios")

            title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
            subtitle_format = workbook.add_format({'italic': True, 'font_size': 12, 'align': 'left'})
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'align': 'center', 'border': 1})
            data_format = workbook.add_format({'align': 'center', 'border': 1})

            worksheet.merge_range('A1:F1', f"Reporte {current_company.name.upper()} de Precios", title_format)
            worksheet.merge_range('A2:F2', f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}", subtitle_format)

            for col_num, column in enumerate(df.columns):
                worksheet.write(2, col_num, column, header_format)

            for row_num, row_data in enumerate(df.values, start=3):
                for col_num, cell_value in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_value, data_format)

            # Ajustar el ancho de las columnas
            worksheet.set_column(0, 0, 20)  # COD. EMPRESA
            worksheet.set_column(1, 1, 15)  # COD. PROD.
            worksheet.set_column(2, 2, 10)  # P. MAX.
            worksheet.set_column(3, 3, 10)  # P. MIN.
            worksheet.set_column(4, 4, 10)  # P. MEDIO
            worksheet.set_column(5, 5, 30)  # DESCRIPCIÓN DEL PRODUCTO

            workbook.close()
            output.seek(0)

            # Retornar el archivo como respuesta
            return request.make_response(output.getvalue(), [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="Reporte_Precios.xlsx"')
            ])

        except Exception as e:
            _logger.error("Error al generar el reporte: %s", str(e))
            return request.make_response(
                "Ocurrió un error al generar el reporte.",
                [('Content-Type', 'text/plain')]
            )
