from odoo import http
from odoo.http import request
import io
import xlsxwriter

class MeliProductExportExcelController(http.Controller):

    @http.route('/export/excel/meli/products', type='http', auth='user')
    def export_excel_meli_products(self, ids='', **kwargs):
        if not ids:
            return request.not_found()

        ids_list = [int(i) for i in ids.split(',') if i.isdigit()]
        records = request.env['mercado.libre.product'].browse(ids_list)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('LIST PRICING')

        # Estilo encabezado
        bold = workbook.add_format({'bold': True})

        headers = ['CODE', 'NAME PRODUCT', 'NEW PRICE', 'ESTADO']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold)

        for row, rec in enumerate(records, start=1):
            text =""
            if rec.price_score == "A":
                text = "Encima del promedio"
            elif rec.price_score == "B":
                text = "En el promedio"
            elif rec.price_score == "C":
                text = "Bajo del promedio"
            worksheet.write(row, 0, rec.product.ml_publication_code or '')
            worksheet.write(row, 1, rec.product.name or '')
            worksheet.write(row, 2, rec.new_price or 0.0)
            worksheet.write(row, 3, text)

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="pricing_list.xlsx"')
            ]
        )
