/* @odoo-module */

import { patch } from '@web/core/utils/patch';
import { SIZES } from '@web/core/ui/ui_service';
import { setAttributes } from '@web/core/utils/xml';
import { FormCompiler } from '@web/views/form/form_compiler';


patch(FormCompiler.prototype, {

    compile(node, params) {
        const res = super.compile(node, params);

        const webClientViewAttachmentViewHookXml = res.querySelector('.o_attachment_preview');
        const hasPreview = !!webClientViewAttachmentViewHookXml;

        if (webClientViewAttachmentViewHookXml) {
            const sidedChatterContainerHookXml = res.querySelector('.o_form_renderer > .o-mail-Form-chatter');
            const formSheetBgXml = res.querySelector('.o_form_sheet_bg');

            if (sidedChatterContainerHookXml && formSheetBgXml) {

                setAttributes(formSheetBgXml, {
                    't-att-class': `{'xl_form': __comp__.uiService.size == ${SIZES.XL}}`,
                });

                if (sidedChatterContainerHookXml) {
                    const sidedChatterContainerXml = sidedChatterContainerHookXml.querySelector(
                        "t[t-component='__comp__.mailComponents.Chatter']"
                    );

                    if (sidedChatterContainerXml) {
                        const form = res.querySelector('.o_form_renderer');
                        const attf = form.getAttribute('t-attf-class');
                        form.setAttribute('t-attf-class', attf.replace('? "flex-column"', ` and !(__comp__.uCommboSize and ${hasPreview}) ? "flex-column"`))
                    }
                }
            }
        }

        return res;
    },
});
