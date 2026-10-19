odoo.define('l10n_pe_cpe_form.s_website_form', function (require) {
    'use strict';

    var core = require('web.core');
    var time = require('web.time');
    const {ReCaptcha} = require('google_recaptcha.ReCaptchaV3');
    const session = require('web.session');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    const dom = require('web.dom');
    const concurrency = require('web.concurrency');

    var _t = core._t;
    var qweb = core.qweb;

    publicWidget.registry.s_website_form.include({
        send: async function (e) {
            if (!this.$target.find('.s_website_cpe_form_send')){
                await this._super(...arguments);
            }
            else {
                e.preventDefault(); // Prevent the default submit behavior
                const $button = this.$target.find('.s_website_form_send, .o_website_form_send');
                $button.addClass('disabled') // !compatibility
                       .attr('disabled', 'disabled');
                this.restoreBtnLoading = dom.addButtonLoadingEffect($button[0]);

                var self = this;

                self.$target.find('#s_website_form_result, #o_website_form_result').empty(); // !compatibility
                if (!self.check_error_fields({})) {
                    self.update_status('error', _t("Please fill in the form correctly."));
                    return false;
                }

                this.form_fields = this.$target.serializeArray();
                $.each(this.$target.find('input[type=file]:not([disabled])'), (outer_index, input) => {
                    $.each($(input).prop('files'), function (index, file) {
                        self.form_fields.push({
                            name: input.name + '[' + outer_index + '][' + index + ']',
                            value: file
                        });
                    });
                });
                var form_values = {};
                _.each(this.form_fields, function (input) {
                    if (input.name in form_values) {
                        if (Array.isArray(form_values[input.name])) {
                            form_values[input.name].push(input.value);
                        } else {
                            form_values[input.name] = [form_values[input.name], input.value];
                        }
                    } else {
                        if (input.value !== '') {
                            form_values[input.name] = input.value;
                        }
                    }
                });
                this.$target.find('.s_website_form_field:not(.s_website_form_custom)')
                .find('.s_website_form_date, .s_website_form_datetime').each(function () {
                    const inputEl = this.querySelector('input');
                    /*if (!inputEl.value) {
                        return;
                    }*/
                    var date = $(this).datetimepicker('viewDate').clone().locale('en');
                    var format = 'YYYY-MM-DD';
                    if ($(this).hasClass('s_website_form_datetime')) {
                        date = date.utc();
                        format = 'YYYY-MM-DD HH:mm:ss';
                    }
                    form_values[this.getAttribute('name')] = date.format(format);
                });

                if (this._recaptchaLoaded) {
                    const tokenObj = await this._recaptcha.getToken('website_form');
                    if (tokenObj.token) {
                        form_values['recaptcha_token_response'] = tokenObj.token;
                    } else if (tokenObj.error) {
                        self.update_status('error', tokenObj.error);
                        return false;
                    }
                }

                ajax.post(this.$target.attr('action') + (this.$target.data('force_action') || this.$target.data('model_name')), form_values)
                .then(async function (result_data) {
                    // Restore send button behavior
                    self.$target.find('.s_website_form_send, .o_website_form_send')
                        .removeAttr('disabled')
                        .removeClass('disabled'); // !compatibility
                    result_data = JSON.parse(result_data);
                    if (!result_data.url) {
                        // Failure, the server didn't return the created record ID
                        self.update_status('error', result_data.error ? result_data.error : false);
                        if (result_data.error_fields) {
                            // If the server return a list of bad fields, show these fields for users
                            self.check_error_fields(result_data.error_fields);
                        }
                    } else {
                        // Success, redirect or update status
                        let successMode = 'redirect';
                        let successPage = result_data.url;
                        if (!successMode) {
                            successPage = self.$target.attr('data-success_page'); // Compatibility
                            successMode = successPage ? 'redirect' : 'nothing';
                        }
                        switch (successMode) {
                            case 'redirect': {
                                let hashIndex = successPage.indexOf("#");
                                if (hashIndex > 0) {
                                    let currentUrlPath = window.location.pathname;
                                    if (!currentUrlPath.endsWith("/")) {
                                        currentUrlPath = currentUrlPath + "/";
                                    }
                                    if (!successPage.includes("/#")) {
                                        successPage = successPage.replace("#", "/#");
                                        hashIndex++;
                                    }
                                    if ([successPage, "/" + session.lang_url_code + successPage].some(link => link.startsWith(currentUrlPath + '#'))) {
                                        successPage = successPage.substring(hashIndex);
                                    }
                                }
                                if (successPage.charAt(0) === "#") {
                                    const successAnchorEl = document.getElementById(successPage.substring(1));
                                    if (successAnchorEl) {
                                        await dom.scrollTo(successAnchorEl, {
                                            duration: 500,
                                            extraOffset: 0,
                                        });
                                    }
                                    break;
                                }
                                $(window.location).attr('href', successPage);
                                return;
                            }
                            case 'message': {
                                await concurrency.delay(dom.DEBOUNCE);

                                self.$target[0].classList.add('d-none');
                                self.$target[0].parentElement.querySelector('.s_website_form_end_message').classList.remove('d-none');
                                break;
                            }
                            default: {
                                await concurrency.delay(dom.DEBOUNCE);

                                self.update_status('success');
                                break;
                            }
                        }

                        self.$target[0].reset();
                        self.restoreBtnLoading();
                    }
                })
                .guardedCatch(error => {
                    this.update_status(
                        'error',
                        error.status && error.status === 413 ? _t("Uploaded file is too large.") : "",
                    );
                });

            }

        },

    });
});
