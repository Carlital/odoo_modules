/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { Component, useState, onMounted } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class PDFViewerDialog extends Component {
    setup() {
        this.state = useState({
            isLoading: true,
            viewerUrl: this.getViewerUrl(),
            isMaximized: false
        });
    }

    getViewerUrl() {
        const baseUrl = '/pdf_print_preview/static/lib/pdfjs/web/viewer.html';
        return `${baseUrl}?file=${this.props.url}`;
    }

    onIframeLoad() {
        this.state.isLoading = false;
    }

    toggle() {
        this.state.isMaximized = !this.state.isMaximized;
    }

    getDialogSize() {
        if (this.state.isMaximized) {
            return 'fullscreen';
        }
        return 'xl';
    }

    getFrameStyle() {
        if (this.state.isMaximized) {
            return 'height: calc(98vh - 141px) !important;';
        }
        return 'height: calc(90vh - 100px) !important;';
    }
}

PDFViewerDialog.template = 'pdf_print_preview.PDFViewerDialog';
PDFViewerDialog.components = { Dialog };

// Register for use in actions
registry.category("dialog").add("PDFViewerDialog", PDFViewerDialog);


export function openPDFViewer(env, url, title = "PDF Document") {
    const dialog = env.services.dialog;
    return dialog.add(PDFViewerDialog, {
        url: url,
        title: title
    });
}


/**
 * Helper function to handle automatic printing
 * @param {string} url - URL of the PDF to print
 * @param {Object} env - Environment object for notifications
 */
function handleAutomaticPrinting(url, env) {
    const printFrame = document.createElement('iframe');
    printFrame.style.display = 'none';
    printFrame.src = url;
    
    printFrame.onload = function() {
        try {
            printFrame.contentWindow.print();
        } catch (err) {
            env.services.notification.add(
                _t("Failed to print automatically. Please check your browser settings."),
                {
                    type: 'warning',
                    sticky: true,
                    title: _t("Printing Error"),
                }
            );
            document.body.removeChild(printFrame);
        }
    };

    const cleanup = () => {
        document.body.removeChild(printFrame);
        window.removeEventListener('focus', cleanup);
    };

    window.addEventListener('focus', cleanup);
    
    document.body.appendChild(printFrame);
}


/**
 * Generates the report url given a report action.
 *
 * @private
 * @param {ReportAction} action
 * @param {env} env
 * @returns {string}
 */
function _getReportUrl(action, env, filename) {
    let url = `/report/pdf/${action.report_name}`;
    const actionContext = action.context || {};
    filename = filename || action.name;
     if(filename !== undefined)
        filename = filename.replace(/[/?%#&=]/g, "_") + ".pdf";
    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?filename=${filename}&options=${options}&context=${context}&`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}?filename=${filename}&context=${encodeURIComponent(JSON.stringify(user.context))}&`;
        }
    }

    return url;
}

async function PdfPrintPreview(action, options, env) {
    const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
    const WKHTMLTOPDF_MESSAGES = {
        broken:
            _t(
                "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
                    "in html."
            ) + link,
        install:
            _t(
                "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
            ) + link,
        upgrade:
            _t(
                "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
                    "get a correct display of headers and footers as well as support for " +
                    "table-breaking between pages."
            ) + link,
        workers: _t(
            "You need to start Odoo with at least two workers to print a pdf version of " +
                "the reports."
        ),
    };

    if (action.report_type === "qweb-pdf" && env.services.menu.getCurrentApp() !== undefined && (session.preview_print || session.automatic_printing)) {
        let getReportResult = rpc("/pdf_print_preview/get_report_name", {
            report_name: action.report_name,
            data: JSON.stringify(action.context)
        });
        const result = await getReportResult;
        const state = result["wkhtmltopdf_state"];

        // display a notification according to wkhtmltopdf's state
        if (state in WKHTMLTOPDF_MESSAGES) {
            env.services.notification.add(WKHTMLTOPDF_MESSAGES[state], {
                sticky: true,
                title: _t("Report"),
            });
        }

        if (state === "upgrade" || state === "ok") {
            let url = _getReportUrl(action, env, result["file_name"]);
            if(session.preview_print) {
                // PreviewDialog.createPreviewDialog(self, url,  action.name);
                openPDFViewer(env, url, action.name);
            }

            if (session.automatic_printing) {
                handleAutomaticPrinting(url, env);
            }
            return true;
        }
    }
}

registry
    .category("ir.actions.report handlers")
    .add("pdf_print_preview", PdfPrintPreview);
