from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class ExportData(http.Controller):
    """Este controlador recupera los datos de los campos seleccionados en el diálogo para el informe PDF."""

    @http.route('/get_data', auth="user", type='json')
    def action_get_export_data(self, **kw):
        """
        Método para recuperar los detalles necesarios según los parámetros proporcionados.
        """

        fields = kw.get('fields', [])
        model = kw.get('model')
        orientation = kw.get('orientation', 'portrait')
        Model = request.env[model]

        field_names = [f['name'] for f in fields]
        columns_headers = [val['label'].strip() for val in fields]

        domain = [('id', 'in', kw.get('res_ids', []))] if kw.get('res_ids') else kw.get('domain', [])
        groupby = kw.get('grouped_by', [])

        # Formato de papel según la orientación
        paperformat = request.env.ref('export_view_pdf.paperformat_export_horizontal' if orientation == 'landscape' else 'export_view_pdf.paperformat_export')
        paperformat_id = paperformat.id

        # Actualiza el `paperformat_id`
        action_report = request.env['ir.actions.report'].search([('report_name', '=', 'export_view_pdf.export_in_pdf')], limit=1)
        if action_report:
            action_report.write({'paperformat_id': paperformat_id})

        # Verifica si existen datos agrupados
        if groupby:

            # Configura datos agrupados si existe `groupby`
            groupby_type = [Model._fields[x.split(':')[0]].type for x in groupby]
            groups_data = Model.read_group(domain, [x if x != '.id' else 'id' for x in field_names], groupby, lazy=False)
            group_by = []

            for rec in groups_data:
                ids = Model.search(rec['__domain'])
                list_key = [x for x in rec.keys() if x in field_names and x not in groupby]
                export_data = [ids.export_data(field_names).get('datas', [])]

                group_tuple = (
                    {'count': rec['__count']}, rec.get(groupby[0]),
                    export_data,
                    [(rec[x], field_names.index(x)) for x in list_key]
                )
                group_by.append(group_tuple)

            return {
                'header': columns_headers,
                'data': export_data,
                'type': groupby_type,
                'other': group_by if group_by else [],
                'report_name': 'export_view_pdf.export_in_pdf_group_by',
                'paperformat_id': paperformat_id
            }

        else:
            records = Model.browse(kw.get('res_ids', [])) if kw.get('res_ids') else Model.search(domain)
            export_data = records.export_data(field_names).get('datas', [])

            return {
                'header': columns_headers,
                'data': export_data,
                'other': [],
                'report_name': 'export_view_pdf.export_in_pdf',
                'paperformat_id': paperformat_id
            }
