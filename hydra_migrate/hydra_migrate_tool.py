#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Скрипт миграции данных об аккаунтах и устройствах из csv-выгрузки
из АСР Hydra (http://www.hydra-billing.ru/) в базу данных Smarty

(c) Alexander Larin, 2016
"""

import MySQLdb
import csv
from warnings import filterwarnings
from progress.bar import Bar

DB_HOST = "localhost"
DB_USER = "smarty"
DB_PASSWD = "pasword"
DB_NAME = "smarty"
CLIENT_ID = 1
MAG_ID = 3  # ID устройства MAG в таблице Client-Devices, скрипт рассчитан на случай, когда все устройства - MAG

# формат csv: user ID;account ID;tariff ID
ACCOUNT_USER_FILE = 'billing_customers.csv'
# формат csv: --;account ID;--;MAC;device serial
ACCOUNT_DEVICE_FILE = 'billing_devices.csv'


conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWD, db=DB_NAME)
filterwarnings('ignore', category = MySQLdb.Warning)

# таблица соответствия тариф в smarty -> тарифы в hydra
tariffs_matrix = {
    # HD пакет
    2: (1, 2, 3, 4),
    # SD пакет
    8: (5, 6, 7, 8),
    # Базовый
    7: (9, 10, 11, 12),
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
        self.device_id = MAG_ID
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
    print "NONE tariff for " + str(tariff_id)
    return None


def add_users(users):
    print "Add users"
    bar = Bar('Users', max=len(users))
    cursor = conn.cursor()
    
    query_add_customer = """
        insert into
        tvmiddleware_customer (ext_id, client_id, comment)
        values (%s, %s, %s)
    """
    
    for user in users.values():
        bar.next()
        #print user.ext_id, user.ls, user.id
        cursor.execute(query_add_customer, (int(user.ext_id), int(CLIENT_ID), "USER_%d" % user.ls))
        user.id = cursor.lastrowid
        #print user.ext_id, user.ls, user.id
    cursor.close()
    conn.commit()
    bar.finish()


def add_accounts(users):
    print "Add accounts"
    bar = Bar('Accounts', max=len(users))

    cursor = conn.cursor()

    query_add_account = """
        insert into
        tvmiddleware_account (abonement, client_id, customer_id, allow_login_by_abonement, allow_login_by_device_uid, active)
        values (%s, %s, %s, 1, 1, 1)
    """
    
    for user in users.values():
        bar.next()
        cursor.execute(query_add_account, (user.ls, CLIENT_ID, user.id))
        user.account_id = cursor.lastrowid
        #print user.ls, user.id, user.account_id
    cursor.close()
    conn.commit()
    bar.finish()


def add_device_to_user(devices, users):
    cursor = conn.cursor()
    bar = Bar('Devices', max=len(devices))
    query_add_account = """
        insert into
        tvmiddleware_accountdevice (account_id, device_id, client_id, device_uid)
        values (%s, %s, %s, %s)
    """

    for device in devices:
        bar.next()
        if device.ls not in users:
            print device.ls, " not found!"
            continue
        user = users[device.ls]
        #uid = device.mac + ' ' + device.serial
        uid = device.mac
        args = (user.account_id, device.device_id, CLIENT_ID, uid)
        cursor.execute(query_add_account, args)
    cursor.close()
    conn.commit()
    bar.finish()


def add_device(device, user, serial):
    pass


def add_tariff_to_user(users):
    bar = Bar('Tariffs', max=len(users))
    cursor = conn.cursor()
    query_add_account = """
        insert into
        tvmiddleware_customer_tariffs (customer_id, tariff_id)
        values (%s, %s)
    """
    # cursor.lastrowid
    for user in users.values():
        bar.next()
        for tariff_id in user.tariffs:
            real_id = tariff_id
            if real_id != None:
                cursor.execute(query_add_account, (user.id, real_id))
    
    cursor.close()
    conn.commit()
    bar.finish()

accounts = {}
tariffs = []
with open(ACCOUNT_USER_FILE) as csvfile:
    # формат csv: user ID;account ID;tariff ID
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        if len(row) <= 1:
            continue
        try:
            ls = int(row[1])
        except:
            print "can't parse: %s" % row[1]
            continue
        if ls not in accounts:
            user = User()
            user.ls = ls
            user.ext_id = int(row[0])
            accounts[ls] = user
        tariff_id = convert_tariff(int(row[2]))
        if tariff_id not in accounts[ls].tariffs:
            accounts[ls].tariffs.append(tariff_id)

devices = []
devices_uids = []

with open(ACCOUNT_DEVICE_FILE) as csvfile:
    # формат csv: --;account ID;--;MAC;device serial
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        if len(row) <= 1:
            continue
        try:
            ls = int(row[1])
        except:
            print "can't parse: %s" % row[1]
            continue
        device = Device()
        device.ls = int(row[1])
        if device.ls not in accounts:
            print device.ls, row[4].strip()
            continue
        device.mac = row[3].strip().replace('-', ':').lower()
        if device.mac in devices_uids:
            continue
        device.serial = row[4].strip()
        devices.append(device)
        devices_uids.append(device.mac)

add_users(accounts)
add_accounts(accounts)
add_tariff_to_user(accounts)
add_device_to_user(devices, accounts)
conn.close()


