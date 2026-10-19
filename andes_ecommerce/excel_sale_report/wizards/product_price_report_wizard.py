from odoo import models, fields, _
import logging

_logger = logging.getLogger(__name__)

class ProductPriceReportWizard(models.TransientModel):
    _name = 'product.price.report.wizard'
    _description = 'Product Price Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def generate_excel_report(self):
        try:
            if not self.start_date or not self.end_date:
                return self._show_notification(
                    title=_("Fechas inválidas"),
                    message=_("Por favor, ingrese fechas válidas."),
                    notification_type="danger"
                )

            if self.start_date > self.end_date:
                return self._show_notification(
                    title=_("Periodo inválido"),
                    message=_("La fecha de inicio no puede ser posterior a la fecha de fin."),
                    notification_type="danger"
                )

            download_url = f'/report/excel_sale_report/download_excel?start_date={self.start_date}&end_date={self.end_date}'
            return {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'self',
            }

        except Exception as e:
            _logger.error("Error en generate_excel_report: %s", str(e))
            return self._show_notification(
                title=_("Error"),
                message=_("Ocurrió un error al generar el reporte."),
                notification_type="danger"
            )

    def _show_notification(self, title, message, notification_type="info"):
        """Método para mostrar notificaciones emergentes al usuario."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': False,
            },
        }
