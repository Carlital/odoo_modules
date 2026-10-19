odoo.define('l10n_pe_cpe_form.search_cpe_form', function (require) {
'use strict';

var core = require('web.core');
var FormEditorRegistry = require('website_form.form_editor_registry');

var _t = core._t;

FormEditorRegistry.add('search_cpe', {
    formFields: [{
        type: 'char',
        custom: true,
        name: 'vat',
        string: 'N° Client Document',
    }, {
        type: 'integer',
        modelRequired: true,
        custom: true,
        name: 'number',
        string: 'Number',
    }, {
        type: 'date',
        modelRequired: true,
        name: 'invoice_date',
        string: 'Date Invoice',
    }],
    fields: [{
        name: 'vat',
        type: 'char',
        required: true,
        string: _t('Vat'),
        defaultValue: 'info@yourcompany.example.com',
    }],
});

});

