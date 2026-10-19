odoo.define('l10n_pe_cpe_form.search_cpe_form', function (require) {
'use strict';

var core = require('web.core');
var FormEditorRegistry = require('website.form_editor_registry');

var _t = core._t;

FormEditorRegistry.add('search_cpe', {
    formFields: [{
        type: 'char',
        custom: true,
        name: 'vat',
        string: _t('N° Client Document'),
    }, {
        type: 'float',
        modelRequired: true,
        custom: true,
        name: 'number',
        string: _t('Number'),
    }, {
        type: 'date',
        modelRequired: true,
        name: 'invoice_date',
        string: _t('Date Invoice'),
    }],
    fields: [{
        name: 'vat',
        type: 'char',
        required: true,
        string: _t('Vat'),
    }],
});

});

