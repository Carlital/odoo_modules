# -*- coding: utf-8 -*-

from odoo import models, tools
from odoo.exceptions import ValidationError, UserError
import traceback


class Http(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if tools.config['test_enable'] or tools.config['test_file']:
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

        result = False, False
        messageError = False
        try:
            result = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        except (UserError, ValidationError) as e:
            messageError = str(e)
        except Exception as e:
            messageError = traceback.format_exc()

        if messageError:
            report_ref = "pdf_print_preview.report_error_catcher"
            data = {'error': messageError}
            result = super()._render_qweb_pdf(report_ref, res_ids=[], data=data)
        return result
