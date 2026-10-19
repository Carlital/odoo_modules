/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';
import { useDebounced } from '@web/core/utils/timing';
import { useBus, useService } from '@web/core/utils/hooks';
import { useState } from '@odoo/owl';

import { CheckBox } from '@web/core/checkbox/checkbox';
import { ControlPanel } from '@web/search/control_panel/control_panel';
import { ConfirmationDialog } from '@web/core/confirmation_dialog/confirmation_dialog';

import { useUdooStore, useUdooLocalStore } from '@omux_state_manager/store';

import { useFormStatusIndicatorState } from '../views/form/form_status/indicator';

const RFS_KEY_FRAMES = [
    { opacity: 0.9 },
    { transform: 'translateY(17px)', opacity: 0 },
    { opacity: 1 },
];

patch(ControlPanel.prototype, {

    setup() {
        super.setup();

        if (this.env.services['mail.store']) {
            this.store = useState(useService('mail.store'));
        }
        this.ui = useService('ui');
        this.ue = useUdooLocalStore();
        this.uo = useUdooStore();

        this.store.uQuickRepeat = false;

        useBus(this.env.bus, 'CTL:SRSH', ({ detail }) => {
            const { formIndicatorState } = this;
            if (detail?.skipOnDirty && formIndicatorState && typeof formIndicatorState.displayButtons === 'function' && !!(formIndicatorState.displayButtons())) {
                return;
            }
            this._doRefresh(true);
        });

        this.formIndicatorState = useFormStatusIndicatorState();
        this.doRefresh = useDebounced(this.doRefresh, 200);
    },

    async doRefresh() {
        const { config, searchModel, services } = this.env;
        const { pagerProps, formIndicatorState } = this;

        if (config.viewType == 'form' && formIndicatorState && typeof formIndicatorState.displayButtons === 'function') {
            const hasDataUnsaved = formIndicatorState.displayButtons();
            if (hasDataUnsaved) {
                this.dialogService.add(ConfirmationDialog, {
                    body: _t('There is unsaved data. Do you want to discard the changes and proceed?'),
                    confirm: async () => {
                        await formIndicatorState.discard();
                        return this._doRefresh();
                    },
                    cancel: () => { },
                });
                return;
            }
        }
        return this._doRefresh();
    },

    uInitLayter() {
        this.store.focusChatter = document.querySelectorAll('.o-mail-Form-chatter.o-aside').length > 0;
        this.hasChatter = document.querySelectorAll('.o-mail-Form-chatter').length > 0;
        this.hasAttachmentPreview = document.querySelectorAll('div.o_attachment_preview').length > 0;
        this.hasList = document.querySelectorAll('.o_list_table').length > 0;
    },

    uSwitchAside(dir) {
        this.env.bus.trigger('CHATTER:SWITCH', dir);
        this.uAutoColSize();
    },

    uAutoColSize() {
        window.dispatchEvent(new Event('resize'));
        this.env.bus.trigger('TREE:OMCL');
    },

    uSwitchPopMode() {
        this.ui.dropinMode = !this.ui.dropinMode;
        this.state.dropinMode = this.ui.dropinMode;

        // Hide layter dropdown to renew ui state
        setTimeout(() => {
            this.root.el.querySelector('.u_layter_tg').click();
        }, 140);
    },

    async _doRefresh(silent = false) {
        const { searchModel } = this.env;
        // Refresh effect
        if (!silent) {
            document.querySelector('.o_content')?.animate(RFS_KEY_FRAMES, {
                duration: 300,
                easing: 'ease-out',
            });
        }

        // If has pager try it first
        if (this.pagerProps && typeof this.pagerProps.onUpdate === 'function') {
            const { limit, offset } = this.pagerProps;
            await this.pagerProps.onUpdate({ offset, limit });
        }
        // Other case (setting form, ...)
        else if (searchModel && typeof searchModel.search === 'function') {
            searchModel.search();
        }
        // Other case (ir.actions.report, ir.actions.client)
        else {
            this.actionService.loadState();
        }
    },

    uBackTrick() {
        const backBtn = document.querySelector('.breadcrumb-item.o_back_button');
        if (backBtn) {
            backBtn.click();
        } else {
            this.actionService.restore();
        }
    },

    uQuickRepeatCheck(checked) {
        this.store.uQuickRepeat = checked;
        if (checked) {
        }
    },
});

ControlPanel.components = {
    ...ControlPanel.components,
    CheckBox,
}