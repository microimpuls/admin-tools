# -*- coding: utf-8 -*-

CLIENT_ID = 1
HOST = 'http://127.0.0.1:8180'
API_KEY = 'apikey'
LOG_ENABLED = False

ACCOUNT_ALLOW_LOGIN_BY_ABONEMENT = True
ACCOUNT_ALLOW_MULTIPLE_LOGIN = True
ACCOUNT_ACTIVE = True
ACCOUNT_ALLOW_LOGIN_BY_DEVICE_UID = False

DB_USER = 'AIS_NET'
DB_PASSWORD = 'pass'
DB_HOST = 'example.com'
DB_NAME = 'db'
CURRENT_IP = '127.0.0.1'  # адрес, используемый при вызове MAIN.INIT

tariffs = {
    1: (1, 2, 3),
    2: (4, 5, 6),
}

promo_tariffs = {
    3: (1, 2, 3),
    4: (4, 5, 6),
}
