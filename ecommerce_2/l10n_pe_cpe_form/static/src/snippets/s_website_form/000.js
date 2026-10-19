/** @odoo-module **/

import "@website/snippets/s_website_form/000";  // force deps

import { session } from "@web/session";
import publicWidget from "@web/legacy/js/public/public_widget";
import { delay } from "@web/core/utils/concurrency";
import { _t } from "@web/core/l10n/translation";
import { post } from "@web/core/network/http_service";
import {
    formatDate,
    formatDateTime,
    parseDate,
    parseDateTime,
    serializeDate,
    serializeDateTime,
} from "@web/core/l10n/dates";
import { addLoadingEffect } from "@web/core/utils/ui";
import { scrollTo } from "@web_editor/js/common/scrolling";
const DEBOUNCE = 400;

publicWidget.registry.s_website_form.include({

    /**
     * @override
     */
    send: async function (e) {
        console.log(this)
        if (this.$target.find('.s_website_cpe_form_send').length == 0) {
            await this._super(...arguments);
        }
        else {
            e.preventDefault(); // Prevent the default submit behavior
             // Prevent users from crazy clicking
            const $button = this.$el.find('.s_website_form_send, .o_website_form_send');
            $button.addClass('disabled') // !compatibility
                   .attr('disabled', 'disabled');
            this.restoreBtnLoading = addLoadingEffect($button[0]);

            var self = this;

            self.$el.find('#s_website_form_result, #o_website_form_result').empty(); // !compatibility
            if (!self.check_error_fields({})) {
                if (this.fileInputError) {
                    const errorMessage = this.fileInputError.type === "number"
                        ? _t(
                            "Please fill in the form correctly. You uploaded too many files. (Maximum %s files)",
                            this.fileInputError.limit
                        )
                        : _t(
                            "Please fill in the form correctly. The file “%(file name)s” is too large. (Maximum %(max)s MB)",
                            { "file name": this.fileInputError.fileName, max:this.fileInputError.limit }
                        );
                    this.update_status("error", errorMessage);
                    delete this.fileInputError;
                } else {
                    this.update_status("error", _t("Please fill in the form correctly."));
                }
                return false;
            }

            // Prepare form inputs
            this.form_fields = this.$el.serializeArray();
            $.each(this.$el.find('input[type=file]:not([disabled])'), (outer_index, input) => {
                $.each($(input).prop('files'), function (index, file) {
                    // Index field name as ajax won't accept arrays of files
                    // when aggregating multiple files into a single field value
                    self.form_fields.push({
                        name: input.name + '[' + outer_index + '][' + index + ']',
                        value: file
                    });
                });
            });

            // Serialize form inputs into a single object
            // Aggregate multiple values into arrays
            var form_values = {};
            this.form_fields.forEach((input) => {
                if (input.name in form_values) {
                    // If a value already exists for this field,
                    // we are facing a x2many field, so we store
                    // the values in an array.
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

            // force server date format usage for existing fields
            this.$el.find('.s_website_form_field:not(.s_website_form_custom)')
            .find('.s_website_form_date, .s_website_form_datetime').each(function () {
                const inputEl = this.querySelector('input');
                const { value } = inputEl;
                if (!value) {
                    return;
                }

                form_values[inputEl.getAttribute("name")] = this.matches(".s_website_form_date")
                    ? serializeDate(parseDate(value))
                    : serializeDateTime(parseDateTime(value));
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

            if (odoo.csrf_token) {
                form_values.csrf_token = odoo.csrf_token;
            }

            const formData = new FormData();
            for (const [key, value] of Object.entries(form_values)) {
                formData.append(key, value);
            }

            // Post form and handle result
            post(this.$el.attr('action') + (this.$el.data('force_action') || this.$el.data('model_name')), formData)
            .then(async function (result_data) {
                // Restore send button behavior
                self.$el.find('.s_website_form_send, .o_website_form_send')
                    .removeAttr('disabled')
                    .removeClass('disabled'); // !compatibility
                if (!result_data.id) {
                    // Failure, the server didn't return the created record ID
                    self.update_status('error', result_data.error ? result_data.error : false);
                    if (result_data.error_fields) {
                        // If the server return a list of bad fields, show these fields for users
                        self.check_error_fields(result_data.error_fields);
                    }
                } else {
                    // Success, redirect or update status
                    let successMode = self.el.dataset.successMode;
                    let successPage = self.el.dataset.successPage;
                    if (!successMode) {
                        successPage = self.$el.attr('data-success_page'); // Compatibility
                        successMode = successPage ? 'redirect' : 'nothing';
                    }
                    switch (successMode) {
                        case 'redirect': {
                            $(window.location).attr('href', result_data.url || successPage || '/');
                            return;
                        }
                        case 'message': {
                            // Prevent double-clicking on the send button and
                            // add a upload loading effect (delay before success
                            // message)
                            await delay(DEBOUNCE);

                            self.el.classList.add('d-none');
                            self.el.parentElement.querySelector('.s_website_form_end_message').classList.remove('d-none');
                            break;
                        }
                        default: {
                            // Prevent double-clicking on the send button and
                            // add a upload loading effect (delay before success
                            // message)
                            await delay(DEBOUNCE);

                            self.update_status('success');
                            break;
                        }
                    }

                    self.resetForm();
                    self.restoreBtnLoading();
                }
            })
            .catch(error => {
                this.update_status(
                    'error',
                    error.status && error.status === 413 ? _t("Uploaded file is too large.") : "",
                );
            });
        }
    }
});

