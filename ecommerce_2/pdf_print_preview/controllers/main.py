# -*- coding: utf-8 -*-

import json
import werkzeug.exceptions

from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval, time


class PrintPreviewController(http.Controller):

    @http.route('/pdf_print_preview/get_report_name', type='json', auth='user')
    def get_report_name(self, report_name=False, data={}):
        file_name = ''

        if not report_name:
            raise werkzeug.exceptions.HTTPException(
                description="Cannot found report name in param")

        report = request.env['ir.actions.report']._get_report_from_name(
            report_name)
        if not report:
            raise werkzeug.exceptions.HTTPException(
                description=f"Cannot found report with name ( {report_name} )")

        print_report_name = report.print_report_name
        data = json.loads(data)
        res_ids = data.get('active_ids', [])
        records = request.env[report.model].browse(res_ids)
        try:
            if print_report_name and not len(records) > 1:
                file_name = safe_eval(print_report_name,  {
                                      'object': records, 'time': time})
        except:
            pass

        return {
            'file_name': file_name,
            'wkhtmltopdf_state': request.env['ir.actions.report'].get_wkhtmltopdf_state(),
        }
