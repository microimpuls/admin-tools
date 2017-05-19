#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Скрипт для синхронизации систем биллинга Smarty и Hydra

(c) Alexander Larin, 2016
"""

from smarty_billing_client import BillingAPIException, SmartyBillingAPI
import sys
from datetime import datetime

HOST = 'http://example.com' # release
CLIENT_ID = 1
API_KEY = 'apikey'
LOG_ENABLED = False

ACCOUNT_ALLOW_LOGIN_BY_ABONEMENT = True
ACCOUNT_ALLOW_MULTIPLE_LOGIN = True
ACCOUNT_ACTIVE = True
ACCOUNT_ALLOW_LOGIN_BY_DEVICE_UID = False

tariffs = {
    2: (1, 2, 3, 4),
    3: (5, 6, 7, 8),
}

promo_tariffs = {
    5: (1, 2, 3, 4),
    6: (5, 6, 7, 8),
}

api = SmartyBillingAPI(HOST, CLIENT_ID, API_KEY, LOG_ENABLED)


def get_tariff(tariff, tariff_map):
    try:
        tariff_id = int(tariff)
    except:
        return None
    for key in tariff_map:
        if tariff_id in tariff_map[key]:
            return key
    return None


def get_tariff_list(raw_tariff_list, tariff_map):
    tariff_list = []
    for raw_tariff in raw_tariff_list:
        tariff = get_tariff(raw_tariff, tariff_map)
        if tariff is not None and tariff not in tariff_list:
            tariff_list.append(tariff)
    return tariff_list


def get_inverted_tariff_list(tariff_list, tariff_map):
    out_list = []
    for tariff in tariff_map.keys():
        if tariff not in tariff_list:
            out_list.append(tariff)
    return out_list


def write_log(message):
    if LOG_ENABLED:
        try:
            with open("api_wrapper.log", 'a') as log_file:
                log_file.write("%s : %s\n" % (datetime.now().isoformat(' '), message))
        except:
            pass


def check_user_exists(user_id):
    try:
        api.customer_info(ext_id=user_id)
    except BillingAPIException as e:
            return -1
    return 1


def add_user(user_id):
    api.customer_create(ext_id=user_id, comment="USER_%s" % user_id)


def add_account(user_id, account_id):
    api.account_create(ext_id=user_id, abonement=account_id, allow_login_by_abonement=ACCOUNT_ALLOW_LOGIN_BY_ABONEMENT,
                       active=ACCOUNT_ACTIVE, allow_multiple_login=ACCOUNT_ALLOW_MULTIPLE_LOGIN, 
                       allow_login_by_device_uid=ACCOUNT_ALLOW_LOGIN_BY_DEVICE_UID)
    
    
def assign_tariff(tariff, ext_id):
    api.customer_tariff_assign(tariff, ext_id=ext_id)

    
def remove_tariff(tariff, ext_id):
    api.customer_tariff_remove(tariff, ext_id=ext_id)

    
def create_user_if_not_exists(user_id, account_id):
    error = check_user_exists(user_id)
    if error == 0:
        return
    if error == -1:
        try:
            add_user(user_id)
        except Exception as e:
            write_log(e.message)
    try:
        add_account(user_id, account_id)
    except:
        pass

    
def add_user_tariff(args):
    if len(args) < 3:
        return
    user_id = args[0]
    account_id = args[1]
    raw_tariff_list = args[2].split(',')
    create_user_if_not_exists(user_id, account_id)

    promo_tariff_list = get_tariff_list(raw_tariff_list, promo_tariffs)
    smarty_tariff_list = get_tariff_list(raw_tariff_list, tariffs)
    inverted_promo_tariff_list = get_inverted_tariff_list(promo_tariff_list, promo_tariffs)
        
    for tariff_id in smarty_tariff_list:
        assign_tariff(tariff_id, user_id)
    for promo_tariff_id in inverted_promo_tariff_list:
        assign_tariff(promo_tariff_id, user_id)        
    for promo_tariff_id in promo_tariff_list:
        remove_tariff(promo_tariff_id, user_id)


def remove_user_tariff(args):
    if len(args) < 2:
        return
    user_id = args[0]
    account_id = args[1]    
    create_user_if_not_exists(user_id, account_id)
    
    if len(args) >= 3:
        raw_tariff_list = args[2].split(',')
        promo_tariff_list = get_tariff_list(raw_tariff_list, promo_tariffs)
        smarty_tariff_list = get_tariff_list(raw_tariff_list, tariffs)
    else:
        smarty_tariff_list = tariffs.keys()
        promo_tariff_list = promo_tariffs.keys()

    inverted_promo_tariff_list = get_inverted_tariff_list(promo_tariff_list, promo_tariffs)
    
    for tariff_id in smarty_tariff_list:
        remove_tariff(tariff_id, user_id)
    for promo_tariff_id in inverted_promo_tariff_list:
        remove_tariff(promo_tariff_id, user_id)        
    for promo_tariff in promo_tariff_list:
        assign_tariff(promo_tariff, user_id)

        
def add_user_base_tariff(args):
    pass


def remove_user_base_tariff(args):
    pass


func = {
    'add_user_tariff': add_user_tariff,
    'remove_user_tariff': remove_user_tariff,
    'add_user_base_tariff': add_user_base_tariff,
    'remove_user_base_tariff': remove_user_base_tariff,
}


def handler():
    if len(sys.argv) < 2:
        return
    
    write_log(str(sys.argv))

    func_name = sys.argv[1]
    args = sys.argv[2:]
    if func_name not in func:
        return
    try:
        func[func_name](args)
    except Exception as e:
        write_log(str(e))
handler()
