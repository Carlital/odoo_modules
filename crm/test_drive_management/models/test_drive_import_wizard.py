import base64
import openpyxl
from odoo import models, fields, api
from odoo.exceptions import UserError
from io import BytesIO
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class TestDriveImportWizard(models.TransientModel):
    _name = 'test.drive.import.wizard'
    _description = 'Importar Horario de Prueba de Manejo'

    file = fields.Binary('Archivo', required=True)
    filename = fields.Char('Nombre del Archivo')

    def import_file(self):
        if not self.file:
            raise UserError("Por favor, suba un archivo.")
        
        file_data = base64.b64decode(self.file)
        file_stream = BytesIO(file_data)
        
        wb = openpyxl.load_workbook(file_stream)
        sheet = wb.active
        
        data = []
        for row in sheet.iter_rows(values_only=True):
            data.append(row)
        
        headers = data[0]
        rows = data[1:]
        
        required_columns = ['date', 'time', 'available']
        
        for col in required_columns:
            if col not in headers:
                raise UserError(f"Falta la columna requerida: {col}")
        
        current_datetime = datetime.now()
        
        for idx, row in enumerate(rows, start=2):
            row_dict = dict(zip(headers, row))
            date = row_dict.get('date')
            time = row_dict.get('time')
            available_value = str(row_dict.get('available')).lower()
            available = available_value in ['1', 'true', 'yes']

            try:
                if isinstance(date, datetime):
                    test_drive_date = date.date()
                else:
                    test_drive_date = datetime.strptime(str(date), "%d/%m/%Y").date()

                test_drive_time = datetime.strptime(str(time), "%H").time()
                test_drive_datetime = datetime.combine(test_drive_date, test_drive_time)
            except ValueError as e:
                raise UserError(f"Error al analizar la fecha/hora en la fila {idx}: {e}")

            if test_drive_datetime < current_datetime:
                raise UserError(f"La fila {idx} tiene una fecha/hora pasada: Fecha={date}, Hora={time}")

            _logger.info(f"Importando Horario de Prueba de Manejo: Fecha={date}, Hora={time}, Disponible={available}")

            self.env['test.drive.configuration'].create({
                'date': test_drive_date,
                'time': time,
                'available': available
            })

        _logger.info("Horarios de Prueba de Manejo importados con éxito.")
        self.env['crm.ai'].sudo()._train_model()
