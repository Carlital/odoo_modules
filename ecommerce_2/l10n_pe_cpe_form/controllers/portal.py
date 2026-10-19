
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, content_disposition, route
from base64 import decodebytes
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError, MissingError

class CustomerPortal(CustomerPortal):

    def _show_report(self, model, report_type, report_ref, download=False):
        if report_type in ('pe_edi_zip') and download and report_ref == 'account.account_invoices' and (model.pe_edi_zip):
            report =  decodebytes(model.sudo().pe_edi_zip.datas)
            filename = model.pe_edi_zip.name
            content_type = 'application/zip'
            reporthttpheaders = [
                ('Content-Type', content_type),
                ('Content-Length', len(report)),
            ]
            
            reporthttpheaders.append(('Content-Disposition', content_disposition(filename)))
            return request.make_response(report, headers=reporthttpheaders)
        res = super(CustomerPortal, self)._show_report(model, report_type, report_ref, download)
        return res

class PortalAccount(PortalAccount):
    
    @route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        if report_type and report_type in ('pe_edi_zip'):
            try:
                invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
            except (AccessError, MissingError):
                return request.redirect('/my')
            
            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='account.account_invoices', download=download)
        return super(PortalAccount, self).portal_my_invoice_detail(invoice_id, access_token=access_token, report_type=report_type, download=download, **kw)
    
    
    