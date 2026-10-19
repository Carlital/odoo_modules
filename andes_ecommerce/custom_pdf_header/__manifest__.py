{
    'name': 'Custom PDF Header',
    'version': '1.0',
    'description': 'This module customizes the header of inventory reports and adds an option to print PDFs in horizontal orientation.',
    'summary': 'Customizes the header of inventory reports in PDF exports and adds horizontal print option.',
    'author': 'Carla Lomas',
    'license': 'LGPL-3',
    'category': 'Customization',
    'depends': ['base','web','export_view_pdf'],
    'data': [
        'views/report_templates.xml',
    ],
    'installable': True,
}