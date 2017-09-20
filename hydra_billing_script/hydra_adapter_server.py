# -*- coding: utf-8 -*-

"""
Веб-сервер на Flask для удалённого вызова функций Hydra через HTTP-запросы

(c) Alexander Larin, 2016
"""

from flask import Flask, request
import json
from hydra_adapter import HydraConnection, HydraAdapterError
import datetime
import io
import settings
import adapter_utils

app = Flask(__name__)
app.debug = False

# общие ошибки:
# -1 - неизвестная ошибка
# 0 - нет ошибки
# 1 - неверные параметры


def log(message):
    try:
        message = u"%s : %s \n" % (datetime.datetime.now().isoformat(), message)
        if settings.LOG_ENABLED:
            with io.open('/var/log/microimpuls/hydra.log', 'a', encoding='utf8') as f:
                f.write(message)
        else:
            print message
    except Exception as e:
        print "Can't write log: " + repr(e)


def get_int(param_name):
    try:
        out = int(request.args.get(param_name, -1))
    except:
        out = -1
    return out


def mac_convert(mac):
    return mac.upper().replace(':', '-')


def get_balance(account):
    with HydraConnection() as conn:
        user_id, account_id = conn.get_account_by_ls(account)
        balance = conn.get_balance(account_id)
        servs = conn.get_all_services(user_id, account_id)
        recommended = conn.get_recommended_pay(user_id)
    return balance, servs, recommended


def set_promised_payment(account, login=None, password=None):
    error_code, error = 0, u''
    with HydraConnection() as conn:
        user_id, account_id = conn.get_account_by_ls(account)

        try:
            conn.init_session(user_id)
        except HydraAdapterError:
            return 1002, u"Ошибка авторизации"

        log(u'set_payment: account %s, login %s, password %s, user_id %s' % (account, login, password, str(user_id)))
        
        conn.main_init(login, password)
        
        recommended = conn.get_recommended_pay(user_id)
        if abs(recommended) > 1e-9:
            conn.set_promised_payment(account_id)
            recommended = conn.get_recommended_pay(user_id)
            if abs(recommended) > 1e-9:
                # не смогли установить обещанный платёж
                error_code, error = 1001, u"Ошибка установки обещанного платежа"
        else:
            # нет причин для установки обещанного платежа, рекомендуемый платёж не больше нуля
            error_code, error = 1000, u"Обещанный платёж не требуется"
    return error_code, error


def set_mac_close_date(mac, account):
    with HydraConnection() as conn:
        user_id, account_id = conn.get_account_by_ls(account)
        conn.set_mac_close_date(user_id, mac)


def check_device(conn, user_id, serial, mac):
    """
    0 - проверка успешна
    1 - нет такого устройства в БД
    2 - превышен лимит устройств
    """
    assert(isinstance(conn, HydraConnection))
    stb_list = conn.get_stb_list(user_id)
    packet_list = conn.get_active_billing_packets(user_id)

    # проверяем наличие свободных пакетов (количество пакетов должно быть больше, чем количество приставок)
    if len(packet_list) <= len(stb_list):
        return 2

    # проверяем, что приставка есть в базе у данного пользователя
    mac = mac.lower()
    serial = serial.lower()
    for stb in stb_list:
        if stb[5].lower() == mac and stb[2].lower() == serial:
            return 0
    return 1


def add_device(account, mac, serial):
    with HydraConnection() as conn:
        user_id, account_id = conn.get_account_by_ls(account)
        check_code = check_device(conn, user_id, serial, mac)
        if check_code == 1:
            raise HydraAdapterError(u'Устройство не найдено', 1010)
        if check_code == 2:
            raise HydraAdapterError(u'Превышен лимит устройств', 1011)
        conn.set_mac_and_serial(user_id, mac, serial)


def check_login_pass(account, user, password):
    error = 0
    with HydraConnection() as conn:
        user_id, account_id = conn.get_account_by_ls(account)
        user = conn.get_user_by_login_pass(user, password)
        if user_id != user:
            error = 1000
    return error


def add_tariff(account, tariff):
    error = 0
    removing_list = adapter_utils.get_all_billing_tariffs(tariff, settings.tariffs)
    if len(removing_list) > 0:
        with HydraConnection() as conn:
            goods = conn.get_goods(account)
            tariff_list = map(lambda t: t[0], goods)

            perform_action = False
            for tariff_id in removing_list:
                if tariff_id in tariff_list:
                    tariff_list.remove(tariff_id)
                    perform_action = True
                    
            if perform_action:
                user_id, account_id = conn.get_account_by_ls(account)
                conn.init_session(user_id)
                conn.overwrite_subscriptions(account, tariff_list)
    return error


def remove_tariff(account, tariff):
    error = 0
    tariff_id = adapter_utils.get_any_billing_tariff(tariff, settings.tariffs)
    if tariff_id == -1:
        error = 1010
    else:
        with HydraConnection() as conn:
            goods = conn.get_goods(account)
            tariff_list = map(lambda t: t[0], goods)
            if tariff_id not in tariff_list:
                user_id, account_id = conn.get_account_by_ls(account)
                conn.init_session(user_id)
                conn.overwrite_subscriptions(account, tariff_list)
    return error


@app.route("/check_login_pass", methods=['GET'])
def handler_check_login_pass():
    """
    ошибки:
    2 - аккаунт не найден
    1000 - неверный логин или пароль
    """
    account = request.args.get('account_id', None)
    user = request.args.get('user', None)
    password = request.args.get('pass', None)

    if account is None or user is None or password is None:
        error = 1
    else:
        try:
            error = check_login_pass(account, user, password)
        except HydraAdapterError as e:
            error = e.code
        except Exception as e:
            log(e.message)
            error = -1

    response = {
        "error": error,
    }
    return json.dumps(response)


@app.route("/get_balance", methods=['GET'])
def handler_get_balance():
    """
    ошибки:
    2 - аккаунт не найден
    """
    account = request.args.get('account_id', None)
    log('get_balance %s' % account)

    balance = 0.0
    recommended = 0.0
    servs = []
    error = 0

    if account is None:
        error = 1
    else:
        try:
           balance, servs, recommended = get_balance(account)
        except HydraAdapterError as e:
            error = e.code
        except Exception as e:
            log(e.message)
            error = -1

    responce = {
        "error": error,
        "balance": balance,
        "servs": servs,
        "max_promised_payment": recommended,
        "recommended_payment": recommended,
    }
    log(str(responce))
    return json.dumps(responce, ensure_ascii=False, encoding='utf8')


@app.route("/set_promised_payment", methods=['GET'])
def handler_set_promised_payment():
    """
    ошибки:
    4 - MAC не найден
    1000 - невозможно установить обещанный платёж
    1001 - ошибка установки обещанного платёжа
    1002 - невозможно получить логин или пароль, возможно, не подключен ЛК
    1003 - обещанный платёж не требуется
    """
    account = request.args.get('account_id', None)
    user = request.args.get('user', None)
    password = request.args.get('pass', None)
    log('set_prom %s' % account)

    if account is None:
        error, error_text = 1, u'Неверный запрос'
    else:
        try:
            error, error_text = set_promised_payment(account, user, password)
        except HydraAdapterError as e:
            log(e.message)
            error = e.code
            error_text = e.message
        except Exception as e:
            message = unicode(str(e), "utf8")
            log(message)
            if message.find(u'Обещанный платеж не требуется') < 0:
                error = -1
                error_text = u'Неизвестная ошибка'
            else:
                error = 1003
                error_text = u'Обещанный платёж не требуется'

    response = {
        "error": error_text,
        "error_code": error,
    }
    log(str(response))
    return json.dumps(response, ensure_ascii=False, encoding='utf8')


def tariff_action(action_name, action_func):
    account = request.args.get('account_id', None)
    tariff = request.args.get('tariff_id', None)
    log('%s %s %s' % (action_name, account, tariff))

    error = 0
    if account is None or tariff is None:
        error = 1
    else:
        try:
            action_func(account, tariff)
        except HydraAdapterError as e:
            log(e.message)
            error = e.code
        except Exception as e:
            log(e.message)
            error = -1

    response = {
        "error_code": error,
    }
    log(str(response))
    return json.dumps(response)


@app.route("/add_tariff", methods=['GET'])
def handler_add_tariff():
    """
    ошибки:
    2 - аккаунт не найден
    1000 - тариф не найден
    """
    return tariff_action('add_tariff', add_tariff)


@app.route("/remove_tariff", methods=['GET'])
def handler_remove_tariff():
    """
    ошибки:
    2 - аккаунт не найден
    1000 - тариф не найден
    """
    return tariff_action('remove_tariff', remove_tariff)


@app.route("/add_device", methods=['GET'])
def handler_add_device():
    """
    ошибки:
    2 - аккаунт не найден
    3 - все устройства уже зарегистрированы или устройство не найдено
    4 - MAC не найден
    1010 - устройство не найдено (или привязано не к данному пользователю)
    1011 - превышен лимит устройств (нет свободных пакетов)
    """

    account = request.args.get('account_id', None)
    mac = request.args.get('mac', '')
    mac = mac_convert(mac)
    serial = request.args.get('serial', '')
    log('add_device %s %s %s' % (account, mac, serial))

    error = 0
    if account is None or len(mac) == 0 or len(serial) == 0:
        error = 1
    else:
        try:
            add_device(account, mac, serial)
        except HydraAdapterError as e:
            log(e.message)
            error = e.code
        except Exception as e:
            log(e.message)
            error = -1

    response = {
        "error": error,
    }
    log(str(response))
    return json.dumps(response)


@app.route("/set_mac_close_date", methods=['GET'])
def handler_set_mac_close_date():
    """
    ошибки:
    2 - аккаунт не найден
    4 - MAC не найден
    """
    account = request.args.get('account_id', None)
    mac = request.args.get('mac', '')
    mac = mac_convert(mac)
    log('set_mac_close %s' % mac)

    error = 0
    if len(mac) == 0 or account is None:
        error = 1
    else:
        try:
            set_mac_close_date(mac, account)
        except HydraAdapterError as e:
            log(e.message)
            error = e.code
        except Exception as e:
            log(e.message)
            error = -1

    response = {
        "error": error,
    }
    log(str(response))
    return json.dumps(response)


if __name__ == "__main__":
    app.run()
