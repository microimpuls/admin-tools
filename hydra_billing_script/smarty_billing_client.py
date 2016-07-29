# -*- coding: utf-8 -*-

"""
Библиотека для работы с биллингом Smarty
(c) Alexander Larin, 2016
"""


import json
import urlparse
import hashlib
import base64
import urllib2
import urllib


class BillingAPIException(Exception):
    ArgumentError = -100
    UnknownError = -1
    CustomerNotExists = -2
    TransactionNotExists = -3
    AccountNotExists = -4
    TariffNotExists = -5
    AccountAlreadyExists = -6
    ObjectAlreadyExists = -7

    def __init__(self, code, *args, **kwargs):
        self.code = code
        super(BillingAPIException, self).__init__(args, kwargs)


class SmartyBillingAPI(object):

    def __init__(self, base_url, client_id, api_key, write_log):
        """
        :param base_url: хост smarty, например http://smarty.microimpuls.com
        :param client_id: идентефикатор клиента
        :param api_key: ключ клиента
        """
        self.base_url = base_url
        self.client_id = client_id
        self.api_key = api_key
        self.write_log = write_log

    def _get_signature(self, request_data):
        sign_source = u''
        for (key, value) in sorted(request_data.items()):
            sign_source += u'%s:%s;' % (key, value)
        sign_source += self.api_key
        digester = hashlib.md5()
        sign_source_utf = sign_source.encode('utf-8')
        sign_source_base64 = base64.b64encode(sign_source_utf)
        digester.update(sign_source_base64)
        signature = digester.hexdigest()
        return signature

    def _get_full_url(self, path):
        parsed_base_url = urlparse.urlparse(self.base_url)
        full_url = urlparse.urlunparse(parsed_base_url._replace(path=path))
        return full_url

    def _api_request(self, path, data=None):
        url = self._get_full_url(path)
        data = data or {}
        data['client_id'] = self.client_id
        data['signature'] = self._get_signature(data)
        encoded_post_data = urllib.urlencode(data)
        req = urllib2.Request(url, encoded_post_data)
        response = urllib2.urlopen(req)
        api_response = json.loads(response.read())
        
        if self.write_log:
            try:
                with open("api_wrapper.log", 'a') as log_file:
                    from datetime import datetime
                    log_file.write("%s \nPATH: %s\nDATA: %s\n RESPONSE: %s\n\n" %
                            (datetime.now().isoformat(' '), str(path), str(data), str(api_response)))
            except:
                pass
                
        if api_response['error']:
            error_message = "Api Error %(error)s: %(error_message)s" % api_response 
            raise BillingAPIException(api_response['error'], error_message)
        return api_response

    def transaction_create(self, customer_id, transaction_id, amount=0, comment=''):
        params = {
            'customer_id': customer_id,
            'id': transaction_id,
            'amount': amount,
            'comment': comment
        }
        return self._api_request('/billing/api/transaction/create/', params)

    def transaction_delete(self, customer_id, transaction_id):
        params = {
            'customer_id': customer_id,
            'id': transaction_id,
        }
        return self._api_request('/billing/api/transaction/delete/', params)

    def customer_create(self, **kwargs):
        """ Создание кастомера
        """
        params = {}
        fields = [
            'firstname', 'middlename', 'lastname', 'birthdate',
            'passport_number', 'passport_series', 'passport_issue_date', 'passport_issued_by',
            'postal_address_street', 'postal_address_bld', 'postal_address_apt', 'postal_address_zip',
            'billing_address_street', 'billing_address_bld', 'billing_address_apt', 'billing_address_zip',
            'mobile_phone_number', 'phone_number_1', 'phone_number_2', 'fax_phone_number', 'email', 'company_name',
            'comment', 'auto_activation_period', 'ext_id'
        ]

        for key, value in kwargs.items():
            if key in fields:
                params[key] = value
        required_fields = ['firstname', 'lastname', 'middlename', 'comment']
        if not any(i in params.keys() for i in required_fields):
            raise BillingAPIException(BillingAPIException.ArgumentError,
                                      "You must specify firstname or lastname or middlename or comment")
        return self._api_request('/billing/api/customer/create/', params)

    def customer_info(self, customer_id=-1, ext_id=-1):
        params = {
            'customer_id': customer_id,
            'ext_id': ext_id
        }
        return self._api_request('/billing/api/customer/info/', params)

    def customer_tariff_assign(self, tariff_id, customer_id=-1, ext_id=-1):
        params = {
            'customer_id': customer_id,
            'ext_id': ext_id,
            'tariff_id': tariff_id
        }
        return self._api_request('/billing/api/customer/tariff/assign/', params)

    def customer_tariff_remove(self, tariff_id, customer_id=-1, ext_id=-1):
        params = {
            'customer_id': customer_id,
            'ext_id': ext_id,
            'tariff_id': tariff_id
        }
        return self._api_request('/billing/api/customer/tariff/remove/', params)

    def account_create(self, **kwargs):
        params = {}
        fields = ['password', 'customer_id', 'ext_id', 'active', 'auto_activation_period', 'abonement',
                  'activation_date', 'deactivation_date', 'allow_multiple_login', 'allow_login_by_abonement',
                  'allow_login_by_device_uid', 'data_center', 'parent_code', 'template', 'use_timeshift']

        for key, value in kwargs.items():
            if key in fields:
                params[key] = value
        return self._api_request('/billing/api/account/create/', params)

    def account_delete(self, abonement):
        params = {
            'abonement': abonement
        }
        return self._api_request('/billing/api/account/delete/', params)

    def account_activate(self, abonement):
        params = {
            'abonement': abonement
        }
        return self._api_request('/billing/api/account/activate/', params)

    def account_deactivate(self, abonement):
        params = {
            'abonement': abonement
        }
        return self._api_request('/billing/api/account/deactivate/', params)

    def tariff_list(self):
        return self._api_request('/billing/api/tariff/list/')

