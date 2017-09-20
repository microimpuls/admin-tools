#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Скрипт для синхронизации систем биллинга Smarty и Hydra

(c) Alexander Larin, 2016
"""

from smarty_billing_client import BillingAPIException, SmartyBillingAPI
from hydra_adapter import HydraConnection
import sys
from datetime import datetime
from settings import *
from adapter_utils import *


api = SmartyBillingAPI(HOST, CLIENT_ID, API_KEY, LOG_ENABLED)


def write_log(message):
    if LOG_ENABLED:
        try:
            with open("api_wrapper.log", 'a') as log_file:
                log_file.write("%s : %s\n" % (datetime.now().isoformat(' '), message))
        except:
            pass
    else:
        print "%s : %s\n" % (datetime.now().isoformat(' '), message)


def load_service_list_from_db(account):
    with HydraConnection() as conn:
        user_id, account_id = conn.get_account_by_ls(account)
        conn.init_session(user_id)
        return conn.get_goods(account)


def get_id_from_service_list(service_list):
    # t[0] - ID услуги
    return map(lambda t: t[0], service_list)


def get_customer_name_from_service_list(service_list):
    if len(service_list) > 0:
        # t[4] - ФИО клиента
        return service_list[0][4]
    return None


def update_customer_info(user_id, customer_name):
    api.customer_modify(ext_id=user_id, firstname=customer_name)


def check_user_exists(user_id):
    """
    Проверяет существование пользователя в MW
    """
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


def set_account_state_debt(account_id):
    """
    Деактивирует аккаунт и устанавливает статус 'заблокировано по задолженности'
    """
    api.account_modify(abonement=account_id, active=0, status_reason='DEBT')


def activate_account(account_id):
    """
    Активирует аккаунт и устанавливает статус 'активен'
    """
    api.account_modify(abonement=account_id, active=1, status_reason='ACTIVE')


def assign_tariff(tariff, ext_id):
    api.customer_tariff_assign(tariff, ext_id=ext_id)


def remove_tariff(tariff, ext_id):
    api.customer_tariff_remove(tariff, ext_id=ext_id)


def create_user_if_not_exists(user_id, account_id):
    """
    Создаёт пользователя (customer) и акканут с заданными ID
    """
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

    for tariff_id in smarty_tariff_list:
        remove_tariff(tariff_id, user_id)
    for promo_tariff in promo_tariff_list:
        assign_tariff(promo_tariff, user_id)


def update_user_tariffs(args):
    if len(args) < 2:
        return
    user_id = args[0]
    account_id = args[1]
    create_user_if_not_exists(user_id, account_id)
    service_list = load_service_list_from_db(account_id)
    tariff_list = get_id_from_service_list(service_list)

    # эти тарифы подключаем
    smarty_tariff_list = get_tariff_list(tariff_list, tariffs)
    # остальные отключаем
    inverted_smarty_tariff_list = get_inverted_tariff_list(smarty_tariff_list, promo_tariffs)
    # эти промо-тарифы отключаем
    promo_tariff_list = get_tariff_list(tariff_list, promo_tariffs)
    # остальные возвращаем на место
    inverted_promo_tariff_list = get_inverted_tariff_list(promo_tariff_list, promo_tariffs)

    for tariff_id in smarty_tariff_list:
        assign_tariff(tariff_id, user_id)
    for tariff_id in inverted_smarty_tariff_list:
        remove_tariff(tariff_id, user_id)
    for promo_tariff_id in inverted_promo_tariff_list:
        assign_tariff(promo_tariff_id, user_id)
    for promo_tariff_id in promo_tariff_list:
        remove_tariff(promo_tariff_id, user_id)

    customer_name = get_customer_name_from_service_list(service_list)
    if customer_name:
        update_customer_info(user_id, customer_name)

    if len(smarty_tariff_list) == 0:
        # блокируем пользователя, если у клиента нет ни одного тарифа
        set_account_state_debt(account_id)
    else:
        activate_account(account_id)


def add_user_base_tariff(args):
    # заглушка
    pass


def remove_user_base_tariff(args):
    # заглушка
    pass


func = {
    'update_user_tariffs': update_user_tariffs,
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
        write_log(repr(e))
handler()
