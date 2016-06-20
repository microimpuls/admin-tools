# -*- coding: utf-8 -*-
import requests, json

"""
Скрипт массовой генерации пробных аккаунтов в Microimpuls Middleware
Использует TVMiddleware API интерфейс

(c) Konstantin Shpinev, 2014
"""

CLIENT_ID = 1
API_KEY = ""
ADD_CUSTOMER_URL = "http://smarty.example.com/billing/api/add_customer/"
ADD_ACCOUNT_URL = "http://smarty.example.com/billing/api/add_account/"

COUNT = 25
ACTIVATION_DAYS = 365

for i in range(0, COUNT):
    comment = "365-days CSTB2016 gift card No.%d" % i
    payload = {
        'client_id': CLIENT_ID,
        'api_key': API_KEY,
        'comment': comment,
        'mobile_phone_number': "",
        'send_sms': 0
    }
    r = requests.post(ADD_CUSTOMER_URL, data=payload)
    r = json.loads(r.text)
    customer_id = r['id']

    payload = {
        'client_id': CLIENT_ID,
        'api_key': API_KEY,
        'customer_id': customer_id,
        'auto_activation_period': ACTIVATION_DAYS
    }
    r = requests.post(ADD_ACCOUNT_URL, data=payload)
    r = json.loads(r.text)
    print("%s;%s" % (r['abonement'], r['password']))
