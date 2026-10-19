
from odoo import models


class ReportLETXTAbstract(models.AbstractModel):
    _name = "report.l10n_pe_account.abstract"
    _description = "Abstract Model for TXT reports"

    def _get_objs_for_report(self, docids, data):
        if docids:
            ids = docids
        elif data and "context" in data:
            ids = data["context"].get("active_ids", [])
        else:
            ids = self.env.context.get("active_ids", [])
        return self.env[self.env.context.get("active_model")].browse(ids)

    def create_letxt_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file = ''
        txt_data = self.generate_letxt_report(file, data, objs)
        return txt_data, "letxt"

    def generate_letxt_report(self, file, data, objs):
        raise NotImplementedError()
