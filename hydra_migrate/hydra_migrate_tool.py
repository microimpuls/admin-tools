#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Скрипт миграции данных об аккаунтах и устройствах из csv-выгрузки
из АСР Hydra (http://www.hydra-billing.ru/) в базу данных Smarty

(c) Alexander Larin, 2016
"""

import MySQLdb
import csv


DB_HOST = "localhost"
DB_USER = "smarty"
DB_PASSWD = ""
DB_NAME = "smarty"
CLIENT_ID = 1

ACCOUNT_USER_FILE = ''
ACCOUNT_SERVICE_FILE = 'User_account_services.csv'
ACCOUNT_DEVICE_FILE = 'User_account_devices.csv'


conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWD, db=DB_NAME)
conn.close()

tariffs_matrix = {
    # Базовый
    2: (),
    # Мультиплекс
    3: (),
    # HD
    4: (),
    # HD пакет физлица
    10: (101385201, 268147501, 101385301, 1172785401, 7176543601,
         268147401, 50666001, 101384701, 268166601),
    # HD пакет юрлица
    12: (101385601, 2297358901, 2296974701),
    # SD пакет юрлица
    14: (101385801, 214572001),
    # SD пакет физлица
    17: (101497101, 268166501, 101384701, 268166601),
}


class User:
    def __init__(self):
        self.ls = -1
        self.ext_id = -1
        self.id = -1
        self.account_id = -1
        self.tariffs = []
        self.devices = []


class Device:
    def __init__(self):
        self.ls = -1
        self.device_id = -1
        self.mac = ''
        self.serial = ''


class Tariff:
    def __init__(self):
        self.ls = -1
        self.tariff_id = -1


def convert_tariff(tariff_id):
    for id in tariffs_matrix:
        if tariff_id in tariffs_matrix[id]:
            return id
    return None


def add_users(users):
    cursor = conn.cursor()

    query_add_customer = """
        insert into
        tvmiddleware_customer (ext_id, client_id, comment)
        values (%d, %d, %s)
    """

    for user in users.values():
        cursor.execute(query_add_customer, (user.ext_id, CLIENT_ID, "USER_%s" % user.ls))
        user.id = cursor.lastrowid

    cursor.close()
    conn.commit()


def add_accounts(users):
    cursor = conn.cursor()

    query_add_account = """
        insert into
        tvmiddleware_account (abonement, client_id, customer_id, allow_login_by_abonement)
        values (%d, %d, %d, 1)
    """

    for user in users:
        cursor.execute(query_add_account, (user.ls, CLIENT_ID, user.id))
        user.account_id = cursor.lastrowid

    cursor.close()
    conn.commit()


def add_device_to_user(devices, users): #account_id, device_id, mac):
    cursor = conn.cursor()
    query_add_account = """
        insert into
        tvmiddleware_account (account_id, device_id, client_id, device_uid)
        values (%d, %d, %d, %s)
    """
    # cursor.lastrowid

    for device in devices:
        user = users[device.ls]
        uid = device.mac + ' ' + device.serial
        args = (user.account_id, device.device_id, CLIENT_ID, uid)
        cursor.execute(query_add_account, args)
    cursor.close()


def add_device(device, user, serial):
    pass


def add_tariff_to_user(tariffs, users): #tariff, user):
    cursor = conn.cursor()
    query_add_account = """
        insert into
        tvmiddleware_customer_tariffs (customer_id, tariff_id)
        values (%d, %d)
    """
    # cursor.lastrowid

    for tariff in tariffs:
        tariff_id = tariffs_matrix[tariff.tariff_id]
        user = users[tariff.ls]
        cursor.execute(query_add_account, (user.id, tariff_id))

    cursor.close()


accounts = {}
with open(ACCOUNT_USER_FILE) as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        user = User()
        #user.ls = row[0]
        #user.ext_id = row[1]
        accounts[user.ls] = user

tariffs = []
with open(ACCOUNT_SERVICE_FILE) as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        tariff = Tariff()
        tariff.ls = row[0]
        tariff.tariff_id = row[1]
        tariffs.append(tariff)

devices = []
with open(ACCOUNT_DEVICE_FILE) as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        device = Device()
        device.ls = row[1]
        device.mac = row[4]
        device.serial = row[5]
        devices.append(device)

add_users(accounts)
add_accounts(accounts)
add_tariff_to_user(tariffs, accounts)
add_device_to_user(devices, accounts)

# select N_USER_ID,VC_LOGIN,VC_GOOD_NAME from SS_V_USERS_APP_BINDS where VC_APPLICATION = 'NETSERV_ARM_Private_Office' and  ROWNUM < 20;
