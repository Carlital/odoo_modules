# -*- coding: utf-8 -*-

import base64
import io
from datetime import date, timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class SaleExtendedReportExcelWizard(models.TransientModel):
    _name = 'sale.extended.report.excel.wizard'
    _description = 'Wizard: Reporte de Ventas Extendido en Excel'

    def _default_date_from(self):
        return date.today().replace(day=1)

    def _default_date_to(self):
        return date.today()

    date_from = fields.Date(
        string='Fecha de inicio',
        required=True,
        default=_default_date_from
    )
    date_to = fields.Date(
        string='Fecha final',
        required=True,
        default=_default_date_to
    )

    # Campos para almacenar el archivo generado
    file_data = fields.Binary('Archivo Excel', readonly=True)
    file_name = fields.Char('Nombre del archivo', readonly=True)

    def _generate_main_report_sheet(self, workbook, records):
        worksheet = workbook.add_worksheet('Reporte de Ventas')

        # Formatos para el Excel
        header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#e69138',
                                            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        cell_wrap_format = workbook.add_format(
            {'border': 1, 'valign': 'top', 'text_wrap': True})
        cell_format = workbook.add_format({'border': 1, 'valign': 'top'})
        date_format = workbook.add_format(
            {'border': 1, 'num_format': 'dd/mm/yyyy hh:mm:ss', 'valign': 'top'})
        money_format = workbook.add_format(
            {'border': 1, 'num_format': '#,##0.00', 'valign': 'top'})
        report_header_label_format = workbook.add_format(
            {'bold': True, 'valign': 'top', 'border': 1})
        report_header_date_format = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'valign': 'top', 'border': 1})

        # Escribir la cabecera del reporte
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 30)
        worksheet.write('A1', 'EMPRESA:', report_header_label_format)
        worksheet.write('B1', self.env.company.name)
        worksheet.write('A2', 'GENERADO POR:', report_header_label_format)
        worksheet.write('B2', self.env.user.name)
        worksheet.write('A3', 'FECHA INICIO:', report_header_label_format)
        worksheet.write('B3', self.date_from, report_header_date_format)
        worksheet.write('A4', 'FECHA FINAL:', report_header_label_format)
        worksheet.write('B4', self.date_to, report_header_date_format)

        table_start_row = 5

        # Definición de columnas para mayor mantenibilidad
        columns = [
            {'header': 'Nº de Pedido', 'width': 20, 'format': cell_format,
                'accessor': lambda r: r.name or ''},
            {'header': 'Fecha', 'width': 18, 'format': date_format,
                'accessor': lambda r: r.date_order},
            {'header': 'Asesor(es)', 'width': 30, 'format': cell_wrap_format,
             'accessor': lambda r: r.advisors or ''},
            {'header': 'Cliente', 'width': 30, 'format': cell_format,
                'accessor': lambda r: r.partner_id.name or ''},
            {'header': 'RUC/DNI', 'width': 15, 'format': cell_format,
                'accessor': lambda r: r.vat or ''},
            {'header': 'Rubro', 'width': 30, 'format': cell_wrap_format,
                'accessor': lambda r: r.rubro_ids or ''},
            {'header': 'Dirección', 'width': 40, 'format': cell_format,
                'accessor': lambda r: r.address or ''},
            {'header': 'Canal de Contacto', 'width': 20, 'format': cell_format,
                'accessor': lambda r: r.source_id.name or ''},
            {'header': 'Contacto', 'width': 30, 'format': cell_format,
                'accessor': lambda r: r.contact_name or ''},
            {'header': 'Cargo', 'width': 20, 'format': cell_format,
                'accessor': lambda r: r.contact_function or ''},
            {'header': 'Teléfono', 'width': 15, 'format': cell_format,
                'accessor': lambda r: r.contact_mobile or ''},
            {'header': 'Correo', 'width': 30, 'format': cell_format,
                'accessor': lambda r: r.contact_email or ''},
            {'header': 'Productos cotizados', 'width': 50, 'format': cell_wrap_format,
                'accessor': lambda r: r.quoted_products or ''},
            {'header': 'Moneda', 'width': 10, 'format': cell_format,
                'accessor': lambda r: r.currency_id.symbol or ''},
            {'header': 'Monto - Sub Total', 'width': 18,
                'format': money_format, 'accessor': lambda r: r.amount_untaxed},
            {'header': 'Estado de cotización', 'width': 20, 'format': cell_format, 'accessor': lambda r: dict(
                r._fields['quotation_state'].selection).get(r.quotation_state, '')},
            {'header': 'Motivo de no compra', 'width': 30,
                'format': cell_format, 'accessor': lambda r: r.lost_reason or ''},
        ]

        # Escribir cabeceras de la tabla
        for col_num, col_def in enumerate(columns):
            worksheet.set_column(col_num, col_num, col_def['width'])
            worksheet.write(table_start_row, col_num,
                            col_def['header'], header_format)

        # Escribir filas de datos
        row_num = table_start_row + 1
        for rec in records:
            for col_num, col_def in enumerate(columns):
                value = col_def['accessor'](rec)
                worksheet.write(row_num, col_num, value, col_def['format'])
            row_num += 1

    def _write_summary_sheet(self, workbook, data, sheet_name, header_color, column_titles):
        """
        Escribe una hoja de resumen genérica en el libro de Excel a partir de datos pre-agrupados.

        :param workbook: El objeto workbook de xlsxwriter.
        :param data: Un diccionario con los datos agrupados.
                   Ej: {'Asesor 1': {'pen_total': 100, 'usd_only': 50, 'pen_only': 20}}
        :param sheet_name: El nombre para la nueva hoja.
        :param header_color: El color de fondo para la cabecera.
        :param column_titles: Una lista con los títulos de las 4 columnas.
        """
        # 1. Crear la hoja y formatos
        worksheet = workbook.add_worksheet(sheet_name)
        header_format = workbook.add_format(
            {'bold': True, 'font_color': 'white', 'bg_color': header_color, 'border': 1, 'align': 'center'})
        total_format = workbook.add_format(
            {'bold': True, 'border': 1, 'num_format': '#,##0.00'})
        money_pen_format = workbook.add_format(
            {'border': 1, 'num_format': '"S/" #,##0.00'})
        money_usd_format = workbook.add_format(
            {'border': 1, 'num_format': '"$" #,##0.00'})
        text_format = workbook.add_format(
            {'border': 1})

        # 2. Escribir cabeceras
        headers = [
            (column_titles[0], 35),
            (column_titles[1], 20),
            (column_titles[2], 20),
            (column_titles[3], 20),
        ]
        for col, (header, width) in enumerate(headers):
            worksheet.set_column(col, col, width)
            worksheet.write(0, col, header, header_format)

        # 3. Escribir datos y calcular totales
        row_num = 1
        grand_total_pen_total = 0.0
        grand_total_usd_only = 0.0
        grand_total_pen_only = 0.0

        for key, amounts in sorted(data.items()):
            worksheet.write(row_num, 0, key, text_format)
            worksheet.write(row_num, 1, amounts.get(
                'pen_only', 0.0), money_pen_format)
            worksheet.write(row_num, 2, amounts.get(
                'usd_only', 0.0), money_usd_format)
            worksheet.write(row_num, 3, amounts['pen_total'], money_pen_format)

            grand_total_pen_total += amounts['pen_total']
            grand_total_usd_only += amounts.get('usd_only', 0.0)
            grand_total_pen_only += amounts.get('pen_only', 0.0)
            row_num += 1

        # 4. Escribir la fila de totales
        worksheet.write(row_num, 0, 'TOTAL', total_format)
        worksheet.write(row_num, 1, grand_total_pen_only, money_pen_format)
        worksheet.write(row_num, 2, grand_total_usd_only, money_usd_format)
        worksheet.write(row_num, 3, grand_total_pen_total, money_pen_format)

    def _generate_summary_sheet(self, workbook, commission_records):
        # 1. Agregar los datos por asesor
        sales_by_advisor = {}
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        company_currency = self.env.company.currency_id

        for rec in commission_records:
            if not rec.seller_id:
                continue

            advisor_name = rec.seller_id.name
            if advisor_name not in sales_by_advisor:
                sales_by_advisor[advisor_name] = {
                    'pen_total': 0.0,
                    'usd_only': 0.0,
                    'pen_only': 0.0,
                }

            sales_by_advisor[advisor_name]['pen_total'] += rec.sale_part_pen
            if usd_currency and rec.currency_id == usd_currency:
                sales_by_advisor[advisor_name]['usd_only'] += rec.sale_part_original_currency
            if rec.currency_id == company_currency:
                sales_by_advisor[advisor_name]['pen_only'] += rec.sale_part_pen

        # 2. Escribir la hoja usando el método auxiliar
        self._write_summary_sheet(
            workbook,
            sales_by_advisor,
            'Ventas por asesor',
            '#e69138',
            ['ASESOR', 'Ventas en soles', 'Ventas en dólares', 'Total ventas en soles']
        )

    def _generate_summary_by_key_sheet(self, workbook, records, sheet_name, group_key_lambda, header_color, column_titles):
        """
        Genera una hoja de resumen genérica agrupando por una clave.
        Agrupa los registros, calcula totales por moneda de origen y un total general convertido.
        """
        # 1. Agrupar datos
        data_by_key = {}
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        company_currency = self.env.company.currency_id

        for rec in records:
            key = group_key_lambda(rec)
            if key not in data_by_key:
                data_by_key[key] = {
                    'pen_sales': 0.0,  # Ventas originadas en PEN
                    'usd_sales': 0.0,  # Ventas originadas en USD
                    'total_pen': 0.0,  # Todas las ventas convertidas a PEN
                }

            total_pen_amount = rec.amount_untaxed * \
                (rec.acs_type_exchange or 1.0)
            data_by_key[key]['total_pen'] += total_pen_amount

            if rec.currency_id == company_currency:
                data_by_key[key]['pen_sales'] += rec.amount_untaxed
            elif usd_currency and rec.currency_id == usd_currency:
                data_by_key[key]['usd_sales'] += rec.amount_untaxed

        # 2. Crear la hoja y formatos
        worksheet = workbook.add_worksheet(sheet_name)
        header_format = workbook.add_format(
            {'bold': True, 'font_color': 'white', 'bg_color': header_color, 'border': 1, 'align': 'center'})
        total_format = workbook.add_format(
            {'bold': True, 'border': 1, 'num_format': '#,##0.00'})
        money_pen_format = workbook.add_format(
            {'border': 1, 'num_format': '"S/" #,##0.00'})
        money_usd_format = workbook.add_format(
            {'border': 1, 'num_format': '"$" #,##0.00'})
        text_format = workbook.add_format(
            {'border': 1})

        # 3. Escribir cabeceras
        headers = [
            (column_titles[0], 35),
            (column_titles[1], 20),
            (column_titles[2], 20),
            (column_titles[3], 20),
        ]
        for col, (header, width) in enumerate(headers):
            worksheet.set_column(col, col, width)
            worksheet.write(0, col, header, header_format)

        # 4. Escribir datos y calcular totales generales
        row_num = 1
        grand_total_pen, grand_total_usd, grand_total_all_pen = 0.0, 0.0, 0.0

        for key, amounts in sorted(data_by_key.items()):
            worksheet.write(row_num, 0, key, text_format)
            worksheet.write(row_num, 1, amounts['pen_sales'], money_pen_format)
            worksheet.write(row_num, 2, amounts['usd_sales'], money_usd_format)
            worksheet.write(row_num, 3, amounts['total_pen'], money_pen_format)
            grand_total_pen += amounts['pen_sales']
            grand_total_usd += amounts['usd_sales']
            grand_total_all_pen += amounts['total_pen']
            row_num += 1

        # 5. Escribir fila de totales
        worksheet.write(row_num, 0, 'TOTAL', total_format)
        worksheet.write(row_num, 1, grand_total_pen, money_pen_format)
        worksheet.write(row_num, 2, grand_total_usd, money_usd_format)
        worksheet.write(row_num, 3, grand_total_all_pen, money_pen_format)

    def _generate_sales_by_channel_sheet(self, workbook, records):
        """Genera la hoja de reporte 'Ventas por canal'."""
        self._generate_summary_by_key_sheet(
            workbook=workbook,
            records=records,
            sheet_name='Ventas por canal',
            group_key_lambda=lambda r: r.source_id.name or 'Sin Canal',
            header_color='#e69138',
            column_titles=[
                'Canal de ventas',
                'Ventas en soles',
                'Ventas en dólares',
                'Total ventas en soles',
            ]
        )

    def _generate_quotes_by_advisor_sheet(self, workbook, records):
        """Genera la hoja de reporte 'Cotizaciones por asesor'."""
        # 1. Agrupar datos por asesor de todas las cotizaciones
        quotes_by_advisor = {}
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        company_currency = self.env.company.currency_id

        for rec in records:
            # Procesar Vendedor 1
            if rec.user_id and rec.x_sale_part_pen_seller1 > 0:
                advisor_name = rec.user_id.name
                if advisor_name not in quotes_by_advisor:
                    quotes_by_advisor[advisor_name] = {
                        'pen_total': 0.0, 'usd_only': 0.0, 'pen_only': 0.0}

                quotes_by_advisor[advisor_name]['pen_total'] += rec.x_sale_part_pen_seller1
                if usd_currency and rec.currency_id == usd_currency:
                    quotes_by_advisor[advisor_name]['usd_only'] += rec.x_sale_part_seller1
                if rec.currency_id == company_currency:
                    quotes_by_advisor[advisor_name]['pen_only'] += rec.x_sale_part_pen_seller1

            # Procesar Vendedor 2
            if rec.x_seller2_id and rec.x_sale_part_pen_seller2 > 0:
                advisor_name = rec.x_seller2_id.name
                if advisor_name not in quotes_by_advisor:
                    quotes_by_advisor[advisor_name] = {
                        'pen_total': 0.0, 'usd_only': 0.0, 'pen_only': 0.0}

                quotes_by_advisor[advisor_name]['pen_total'] += rec.x_sale_part_pen_seller2
                if usd_currency and rec.currency_id == usd_currency:
                    quotes_by_advisor[advisor_name]['usd_only'] += rec.x_sale_part_seller2
                if rec.currency_id == company_currency:
                    quotes_by_advisor[advisor_name]['pen_only'] += rec.x_sale_part_pen_seller2

        # 2. Escribir la hoja usando el método auxiliar
        self._write_summary_sheet(
            workbook,
            quotes_by_advisor,
            'Cotizaciones por asesor',
            '#e69138',
            ['ASESOR', 'Cotizado en soles',
                'Cotizado en dólares', 'Total cotizado en soles']
        )

    def _generate_quotes_by_channel_sheet(self, workbook, records):
        """Genera la hoja de reporte 'Cotizaciones por canal'."""
        self._generate_summary_by_key_sheet(
            workbook=workbook,
            records=records,
            sheet_name='Cotizaciones por canal',
            group_key_lambda=lambda r: r.source_id.name or 'Sin Canal',
            header_color='#e69138',
            column_titles=[
                'Canal de ventas',
                'Cotizado en soles',
                'Cotizado en dólares',
                'Total cotizado en soles',
            ]
        )

    def _generate_final_commissions_sheet(self, workbook, commission_records):
        """Genera la hoja de 'Comisiones finales por vendedor'."""
        company = self.env.company
        usd_currency = self.env.ref('base.USD')
        pen_currency = company.currency_id

        # Obtener la tasa de cambio de hoy para la cabecera y cálculos finales
        today_usd_rate = self.env['res.currency']._get_conversion_rate(
            usd_currency, pen_currency, company, date.today())

        # Ajustar el valor de la comisión según lo solicitado
        commission_rate = company.acs_commission / 100.0

        # 1. Agrupar datos y calcular totales por asesor
        advisor_totals = {}
        for rec in commission_records:
            advisor_name = rec.seller_id.name
            if not advisor_name:
                continue

            if advisor_name not in advisor_totals:
                advisor_totals[advisor_name] = {
                    'sales_pen_part': 0.0,  # Suma de partes de venta originadas en PEN
                    'sales_usd_part': 0.0,  # Suma de partes de venta originadas en USD
                    'total_sales_pen': 0.0,  # Gran total de partes de venta convertido a PEN
                    'total_sales_usd': 0.0,  # Gran total de partes de venta convertido a USD
                    'difference_usd': 0.0,  # Diferencia contra la valla de ventas
                    'commission_usd': 0.0,
                    'commission_pen': 0.0,
                }

            # Acumular partes de venta en su moneda original
            if rec.currency_id == pen_currency:
                advisor_totals[advisor_name]['sales_pen_part'] += rec.sale_part_original_currency
                # Convertir la parte de venta de PEN a USD para el total en USD
                rate_on_date = self.env['res.currency']._get_conversion_rate(
                    pen_currency, usd_currency, company, rec.date_order.date())
                advisor_totals[advisor_name]['total_sales_usd'] += rec.sale_part_original_currency * rate_on_date
                advisor_totals[advisor_name]['total_sales_pen'] += rec.sale_part_original_currency
            else:  # Asumimos que es USD
                advisor_totals[advisor_name]['sales_usd_part'] += rec.sale_part_original_currency
                advisor_totals[advisor_name]['total_sales_usd'] += rec.sale_part_original_currency
                # Convertir la parte de venta de USD a PEN para el total en PEN
                advisor_totals[advisor_name]['total_sales_pen'] += rec.sale_part_pen

        # 2. Calcular la comisión final para cada asesor
        for advisor, totals in advisor_totals.items():
            # Nueva columna "Diferencia en Dolares"
            totals['difference_usd'] = totals['total_sales_usd'] - \
                company.acs_sales_meta_monthly_usd
            # "Comisión en dolares" = "Diferencia en Dolares" * Comisión
            totals['commission_usd'] = totals['difference_usd'] * commission_rate
            # "Comisión en soles" = "Comisión en dolares" * Tasa de cambio
            totals['commission_pen'] = totals['commission_usd'] * today_usd_rate

        # 3. Crear la hoja y formatos
        worksheet = workbook.add_worksheet('Comisiones finales por vendedor')
        header_format = workbook.add_format(
            {'bold': True, 'font_color': 'white', 'bg_color': '#0070c0', 'border': 1, 'align': 'center'})
        total_format = workbook.add_format(
            {'bold': True, 'border': 1, 'num_format': '#,##0.00'})
        money_pen_format = workbook.add_format(
            {'border': 1, 'num_format': '"S/" #,##0.00'})
        money_usd_format = workbook.add_format(
            {'border': 1, 'num_format': '"$" #,##0.00'})
        # Formatos con colores de fondo para celdas específicas
        money_usd_highlight_format = workbook.add_format(
            {'border': 1, 'num_format': '"$" #,##0.00', 'bg_color': '#81d41a'})
        money_pen_highlight_format = workbook.add_format(
            {'border': 1, 'num_format': '"S/" #,##0.00', 'bg_color': '#ffff00'})

        percent_format = workbook.add_format(
            {'border': 1, 'num_format': '0.00%'})
        label_format = workbook.add_format({'bold': True, 'border': 1})
        date_format = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'border': 1})
        text_format = workbook.add_format({'border': 1})

        # 4. Escribir cabecera del reporte
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:H', 20)
        worksheet.write('A1', 'Fecha de reporte:', label_format)
        worksheet.write('B1', date.today(), date_format)
        worksheet.write('A2', 'Tasa de cambio (USD a PEN):', label_format)
        worksheet.write('B2', today_usd_rate, workbook.add_format(
            {'num_format': '#,##0.0000'}))
        worksheet.write('A3', 'Comisión:', label_format)
        worksheet.write('B3', commission_rate, percent_format)
        worksheet.write('A4', 'Valla de ventas en USD:', label_format)
        worksheet.write(
            'B4', company.acs_sales_meta_monthly_usd, money_usd_format)

        # 5. Escribir cabeceras de la tabla
        table_start_row = 6
        headers = [
            'ASESOR', 'Ventas en soles (parte)', 'Ventas en dolares (parte)',
            'Total Venta en dolares', 'Total venta en soles', 'Diferencia en Dolares',
            'Comision en dolares', 'Comisión en soles'
        ]
        for col, header in enumerate(headers):
            worksheet.write(table_start_row, col, header, header_format)

        # 6. Escribir datos y calcular totales generales
        row_num = table_start_row + 1
        grand_totals = {
            'sales_pen_part': 0.0, 'sales_usd_part': 0.0, 'total_sales_usd': 0.0,
            'total_sales_pen': 0.0, 'difference_usd': 0.0, 'commission_usd': 0.0,
            'commission_pen': 0.0
        }
        for advisor_name, amounts in sorted(advisor_totals.items()):
            worksheet.write(row_num, 0, advisor_name, text_format)
            worksheet.write(
                row_num, 1, amounts['sales_pen_part'], money_pen_format)
            worksheet.write(
                row_num, 2, amounts['sales_usd_part'], money_usd_format)
            worksheet.write(
                row_num, 3, amounts['total_sales_usd'], money_usd_highlight_format)
            worksheet.write(
                row_num, 4, amounts['total_sales_pen'], money_pen_format)
            worksheet.write(
                row_num, 5, amounts['difference_usd'], money_usd_highlight_format)
            worksheet.write(
                row_num, 6, amounts['commission_usd'], money_usd_highlight_format)
            worksheet.write(
                row_num, 7, amounts['commission_pen'], money_pen_highlight_format)

            for key in grand_totals:
                grand_totals[key] += amounts[key]
            row_num += 1

        # 7. Escribir fila de totales
        worksheet.write(row_num, 0, 'TOTAL', total_format)
        worksheet.write(
            row_num, 1, grand_totals['sales_pen_part'], money_pen_format)
        worksheet.write(
            row_num, 2, grand_totals['sales_usd_part'], money_usd_format)
        worksheet.write(
            row_num, 3, grand_totals['total_sales_usd'], money_usd_highlight_format)
        worksheet.write(
            row_num, 4, grand_totals['total_sales_pen'], money_pen_format)
        worksheet.write(
            row_num, 5, grand_totals['difference_usd'], money_usd_highlight_format)
        worksheet.write(
            row_num, 6, grand_totals['commission_usd'], money_usd_highlight_format)
        worksheet.write(
            row_num, 7, grand_totals['commission_pen'], money_pen_highlight_format)

    def action_export_excel(self):
        self.ensure_one()
        if not xlsxwriter:
            raise UserError(
                _("La librería 'xlsxwriter' es necesaria. Por favor, instálela (`pip3 install xlsxwriter`)."))

        date_to_inclusive = self.date_to + timedelta(days=1)

        main_report_domain = [
            ('date_order', '>=', self.date_from),
            ('date_order', '<', date_to_inclusive),
        ]
        main_records = self.env['sale.extended.report'].search(
            main_report_domain)

        if not main_records:
            raise UserError(
                _("No hay datos para exportar en el rango de fechas seleccionado."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        self._generate_main_report_sheet(workbook, main_records)

        commission_domain = [
            ('date_order', '>=', self.date_from),
            ('date_order', '<', date_to_inclusive),
        ]
        commission_records = self.env['commission.summary'].search(
            commission_domain)

        if commission_records:
            self._generate_summary_sheet(workbook, commission_records)

        # Llamada para generar la nueva hoja "Ventas por canal", asegurando que solo se usen
        # los registros de ventas confirmadas y pagadas.
        if main_records:
            # Obtenemos los IDs de las órdenes de venta que tienen comisiones (es decir, están pagadas)
            paid_sale_order_ids = commission_records.mapped(
                'sale_order_id').ids
            # Filtramos los registros del reporte principal para que coincidan
            paid_main_records = main_records.filtered(
                lambda r: r.sale_order_id.id in paid_sale_order_ids)
            if paid_main_records:
                self._generate_sales_by_channel_sheet(
                    workbook, paid_main_records)

            # --- INICIO: Nuevas hojas de cotizaciones ---
            # Estas hojas usan todos los registros (main_records) sin filtrar por pago.
            self._generate_quotes_by_advisor_sheet(workbook, main_records)
            self._generate_quotes_by_channel_sheet(workbook, main_records)
            # --- FIN: Nuevas hojas de cotizaciones ---

        # Generar la hoja de comisiones finales al final, si hay datos
        if commission_records:
            self._generate_final_commissions_sheet(
                workbook, commission_records)
        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        filename = f"Reporte_Ventas_{self.date_from}_a_{self.date_to}.xlsx"
        self.write({'file_data': file_data, 'file_name': filename})

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=file_data&filename={self.file_name}&download=true',
            'target': 'self',
        }
