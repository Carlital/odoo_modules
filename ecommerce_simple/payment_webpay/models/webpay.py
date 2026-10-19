# -*- coding: utf-'8' "-*-"
import logging
from odoo import api, models, fields
from odoo.tools import float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_repr
from odoo.tools.translate import _
from odoo.addons.payment import utils as payment_utils
from datetime import datetime
from odoo.exceptions import UserError
from werkzeug import urls
_logger = logging.getLogger(__name__)
try:
    from transbank.webpay.webpay_plus.transaction import *
    from transbank.error.transaction_create_error import TransactionCreateError
except Exception as e:
    _logger.warning("No Load transbank: %s" %str(e))


class PaymentAcquirerWebpay(models.Model):
    _inherit = 'payment.acquirer'

    @api.model
    def _get_providers(self,):
        providers = super(PaymentAcquirerWebpay, self)._get_providers()
        return providers

    provider = fields.Selection(
            selection_add=[('webpay', 'Webpay')],
            ondelete={'webpay': 'set default'}
        )
    webpay_commer_code = fields.Char(
            string="Commerce Code"
        )
    webpay_api_key_secret = fields.Char(
            string="Api Secret Key",
        )
    webpay_mode = fields.Selection(
            [
                ('normal', "Normal"),
                ('mall', "Normal Mall"),
                ('oneclick', "OneClick"),
                ('completa', "Completa"),
            ],
            string="Webpay Mode",
            default="normal"
        )

    @api.onchange('webpay_mode')
    def verificar_webpay_mode(self):
        if self.webpay_mode == 'mall':
            ICPSudo = self.env['ir.config_parameter'].sudo()
            if not ICPSudo.get_param(
                        'webpay.commerce_code')\
            or not ICPSudo.get_param(
                        'webpay.private_key')\
            or not ICPSudo.get_param(
                        'webpay.public_cert')\
            or not ICPSudo.get_param(
                        'webpay.cert'):
                raise UserError("No hay configuración definida para Mall")


    def _get_feature_support(self):
        res = super(PaymentAcquirerWebpay, self)._get_feature_support()
        res['fees'].append('webpay')
        return res

    def webpay_compute_fees(self, amount, currency_id, country_id):
        """ Compute paypal fees.

            :param float amount: the amount to pay
            :param integer country_id: an ID of a res.country, or None. This is
                                       the customer's country, to be compared to
                                       the acquirer company country.
            :return float fees: computed fees
        """
        if not self.fees_active:
            return 0.0
        country = self.env['res.country'].browse(country_id)
        if country and self.company_id.country_id.id == country.id:
            percentage = self.fees_dom_var
            fixed = self.fees_dom_fixed
        else:
            percentage = self.fees_int_var
            fixed = self.fees_int_fixed
        fees = (percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
        return fees

    def get_private_key(self):
        webpay_private_key = self.webpay_private_key
        if self.webpay_mode == 'mall':
            ICPSudo = self.env['ir.config_parameter']
            webpay_private_key = ICPSudo.get_param(
                        'webpay.private_key')
        return b64decode(webpay_private_key)

    def get_client(self,):
        if self.state == 'enabled':
            return Transaction().configure_for_production(
                self.webpay_commer_code,
                self.webpay_api_key_secret)
        return Transaction()

    def details(self, client,  post):
        detail = client.factory.create('wsTransactionDetail')
        fees = post.get('fees', 0.0)
        if fees == '':
            fees = 0
        amount = (float(post['amount']) + float(fees))
        currency = self.env['res.currency'].search([
            ('name', '=', post.get('currency', 'CLP')),
        ])
        if self.force_currency and currency != self.force_currency_id:
            amount = lambda price: currency._convert(
                                amount,
                                self.force_currency_id,
                                self.company_id,
                                datetime.now())
            currency = self.force_currency_id
        detail.amount = currency.round(amount)

        detail.commerceCode = self.webpay_commer_code
        detail.buyOrder = post['item_number']
        return [detail]

    def _webpay_make_request(self, payload=None, method='GET'):
        client = self.get_client()
        fees = payload.get('fees', 0.0)
        if fees == '':
            fees = 0
        amount = (float(payload['amount']) + float(fees))
        currency = self.env['res.currency'].search([
            ('name', '=', payload.get('currency', 'CLP')),
        ])
        if self.force_currency and currency != self.force_currency_id:
            amount = currency._convert(
                                amount,
                                self.force_currency_id,
                                self.company_id,
                                datetime.now())
            currency = self.force_currency_id
        return_url = urls.url_join(self.get_base_url(), '/payment/webpay/return')
        response = client.create(
            payload['item_name'],
            payload['item_number'],
            currency.round(amount),
            return_url
        )
        return response

    """
    getTransaction

    Permite obtener el resultado de la transaccion una vez que
    Webpay ha resuelto su autorizacion financiera.
    """
    def getTransaction(self, token):
        client = self.get_client()
        response = client.commit(token)
        return response


class PaymentTxWebpay(models.Model):
    _inherit = 'payment.transaction'

    webpay_txn_type = fields.Selection([
            ('VD', 'Venta Debito'),
            ('VP', 'Venta Prepago'),
            ('VN', 'Venta Normal'),
            ('VC', 'Venta en cuotas'),
            ('SI', '3 cuotas sin interés'),
            ('S2', 'cuotas sin interés'),
            ('NC', 'N Cuotas sin interés'),
        ],
       string="Webpay Tipo Transacción"
    )
    webpay_token = fields.Char(
            string="Webpay Token"
        )
    webpay_date = fields.Datetime(
        string="Webpay Date", readonly=True,)


    @api.model
    def _compute_reference(self, provider, prefix=None, separator='-', **kwargs):
        """ Override of payment to ensure that Webpay requirements for references are satisfied.
        Webpay requirements for references are as follows:
        - References must be unique at provider level for a given merchant account.
          This is satisfied by singularizing the prefix with the current datetime. If two
          transactions are created simultaneously, `_compute_reference` ensures the uniqueness of
          references by suffixing a sequence number.
        :param str provider: The provider of the acquirer handling the transaction
        :param str prefix: The custom prefix used to compute the full reference
        :param str separator: The custom separator used to separate the prefix from the suffix
        :return: The unique reference for the transaction
        :rtype: str
        """
        if provider != 'webpay':
            return super()._compute_reference(provider, prefix=prefix, **kwargs)

        if not prefix:
            # If no prefix is provided, it could mean that a module has passed a kwarg intended for
            # the `_compute_reference_prefix` method, as it is only called if the prefix is empty.
            # We call it manually here because singularizing the prefix would generate a default
            # value if it was empty, hence preventing the method from ever being called and the
            # transaction from received a reference named after the related document.
            prefix = self.sudo()._compute_reference_prefix(provider, separator, **kwargs) or None
        prefix = payment_utils.singularize_reference_prefix(prefix=prefix, max_length=40)
        return super()._compute_reference(provider, prefix=prefix, **kwargs)

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Webpay-specific rendering values.
        Note: self.ensure_one() from `_get_processing_values`
        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.acquirer_id.provider != 'webpay':
            return res
        return_url = urls.url_join(self.acquirer_id.get_base_url(), '/payment/webpay/final')
        api_url = urls.url_join(self.acquirer_id.get_base_url(), '/payment/webpay/redirect')
        rendering_values = {
            'business': self.company_id.name,
            'item_name': self.reference.split('-')[0],
            'item_number': self.reference,
            'amount': self.amount,
            'currency_code': self.currency_id.name,
            'address1': self.partner_address or '',
            'city': self.partner_city or '',
            'country': self.partner_country_id.code or '',
            'email': self.partner_email or '',
            'return_url': return_url,
            'api_url': api_url,
            'tx_id': self.id,
        }

        return rendering_values

    def _send_payment_request(self):
        """ Override of payment to send a payment request to Webpay.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider != 'webpay':
            return

        # Make the payment request
        return_url = urls.url_join(self.acquirer_id.get_base_url(), '/payment/webpay/final')
        data = {
            'business': self.company_id.name,
            'item_name': self.reference.split('-')[0],
            'item_number': self.reference,
            'amount': self.amount,
            'currency_code': self.currency_id.name,
            'address1': self.partner_address or '',
            'city': self.partner_city or '',
            'country': self.partner_country_id.code or '',
            'email': self.partner_email or '',
            'return_url': return_url
        }
        return self.acquirer_id._webpay_make_request(data)

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on Webpay data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'webpay':
            return tx
        txn_id, reference = data['buy_order'], data['session_id']
        if not reference or not txn_id:
            error_msg = _('Webpay: received data with missing reference (%s) or txn_id (%s)') % (reference, txn_id)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        tx = self.search([('reference', '=', reference), ('provider', '=', 'webpay')])
        if not tx:
            raise ValidationError(
                "Webpay: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Webpay data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        """
        super()._process_feedback_data(data)
        if self.provider != 'webpay':
            return
        codes = {
            '0': 'Transacción aprobada.',
            '-1': 'Rechazo de transacción.',
            '-2': 'Transacción debe reintentarse.',
            '-3': 'Rechazo - Interno Transbank.',
            '-4': 'Rechazo - Rechazada por parte del emisor.',
            '-5': 'Rechazo - Transacción con riesgo de posible fraude.',
        }
        status = str(data['response_code'])
        res = {
            'acquirer_reference': data['authorization_code'],
            'webpay_txn_type': data['payment_type_code'],
            'webpay_date': datetime.strptime(data['transaction_date'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            'webpay_token': data['token'],
        }
        self.write(res)
        if status in ['0']:
            _logger.info('Validated webpay payment for tx %s: set as done' % (self.reference))
            self._set_done()
            return True
        elif status in ['-6', '-7']:
            _logger.warning('Received notification for webpay payment %s: set as pending' % (self.reference))
            self._set_pending()
            return True
        elif status in ['-1', '-4']:
            self._set_canceled()
            return False
        else:
            error = 'Received unrecognized status for webpay payment %s: %s, set as error' % (self.reference, codes[status])
            _logger.warning(error)
            return False

    def _confirm_so(self):
        if self.state not in ['cancel']:
            return super(PaymentTxWebpay, self)._confirm_so()
        self._set_canceled()
        return True

    """
    acknowledgeTransaction
    Indica  a Webpay que se ha recibido conforme el resultado de la transaccion
    """
    def acknowledgeTransaction(self, acquirer_id, token):
        client = acquirer_id.get_client()
        datos = client.status(token)
        return datos
