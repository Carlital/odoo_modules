# -*- coding: utf-8 -*-
# from odoo import http


# class AcsValorizadoReport(http.Controller):
#     @http.route('/acs_valorizado_report/acs_valorizado_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/acs_valorizado_report/acs_valorizado_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('acs_valorizado_report.listing', {
#             'root': '/acs_valorizado_report/acs_valorizado_report',
#             'objects': http.request.env['acs_valorizado_report.acs_valorizado_report'].search([]),
#         })

#     @http.route('/acs_valorizado_report/acs_valorizado_report/objects/<model("acs_valorizado_report.acs_valorizado_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('acs_valorizado_report.object', {
#             'object': obj
#         })

