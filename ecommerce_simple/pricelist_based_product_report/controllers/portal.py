from odoo import http, _
from odoo.http import content_disposition, route, request
from odoo.addons.portal.controllers.portal import CustomerPortal
import werkzeug


class CustomerPortal(CustomerPortal):
    
    #@http.route(['/my/pricelist_report/pdf'], type='http', auth="public")
    @http.route(['/my/pricelist_report/csv'], type='http', auth="public")
    def portal_pricelist_report(self):
        url = request.env['pricelist.based.product.report.wizard'].create({}).generate_report_from_website()
        
        csvhttpheaders = [
            ('Content-Type', 'text/csv'),
            ('Content-Length', len(url.json_file)),
            (
                'Content-Disposition',
                content_disposition(url.filename)
            )
        ]
        
        return request.make_response(url.json_file, headers=csvhttpheaders)
        # return werkzeug.utils.redirect(request.httprequest.host_url+url)
