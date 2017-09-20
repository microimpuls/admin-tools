# -*- coding: utf-8 -*-

"""
Библиотека для вызова некоторых функций в системе Hydra напрямую через работу с СУБД
Использует cx_Oracle

(c) Alexander Larin, 2016
"""

import cx_Oracle
import os
import datetime
from settings import *
os.environ["NLS_LANG"] = "Russian_Russia.UTF8"

# имя типа пакета в поле VC_GOOD_TYPE_NAME
PACKET_TYPE_NAME = u'Пакет услуг'


def fine_print(toprint):
    for result in toprint:
        for e in result:
            c = unicode(str(e), "utf8")
            print c,
        print


class HydraAdapterError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class HydraConnection:

    _ADD_SERIAL = u"""
        DECLARE
            num_N_OBJECT_ID SI_OBJECTS.N_OBJECT_ID%TYPE := :obj_id;
        BEGIN
            SI_OBJECTS_PKG.SI_OBJECTS_PUT(
                num_N_OBJECT_ID    => num_N_OBJECT_ID,
                num_N_GOOD_ID      => :good_id,
                vch_VC_SERIAL      => :serial,
                num_N_FIRM_ID      => :firm_id,
                num_N_OWNER_ID     => :owner_id);
        END;
    """

    _ADD_MAC = u"""
        DECLARE
            num_N_ADDRESS_ID  SI_ADDRESSES.N_ADDRESS_ID%TYPE;
            num_N_ADDR_ADDRESS_ID         SI_ADDR_ADDRESSES.N_ADDR_ADDRESS_ID%TYPE;
            num_N_OBJ_ADDRESS_ID          SI_V_OBJ_ADDRESSES.N_OBJ_ADDRESS_ID%TYPE;
        BEGIN
            num_N_ADDR_ADDRESS_ID := NULL;
            SI_ADDRESSES_PKG.SI_ADDRESSES_PUT(
            NUM_N_ADDR_ADDRESS_ID => num_N_ADDR_ADDRESS_ID,
            num_N_ADDRESS_ID   => num_N_ADDRESS_ID,
            num_N_ADDR_TYPE_ID => SS_CONSTANTS_PKG_S.ADDR_TYPE_MAC,
            vch_VC_CODE        => :mac);

            SI_ADDRESSES_PKG.SI_OBJ_ADDRESSES_PUT(
                num_N_OBJ_ADDRESS_ID   => num_N_OBJ_ADDRESS_ID,
                num_N_OBJECT_ID        => :port_id,
                num_N_ADDRESS_ID       => num_N_ADDRESS_ID,
                num_N_OBJ_ADDR_TYPE_ID => SYS_CONTEXT('CONST', 'BIND_ADDR_TYPE_Actual'),
                num_N_ADDR_STATE_ID    => SYS_CONTEXT('CONST', 'ADDR_STATE_On'));
        END;
    """

    _QUERY_CLOSE_MAC = u"""
        DECLARE
        BEGIN
            SI_ADDRESSES_PKG.SI_OBJ_ADDRESSES_PUT(
                num_N_OBJ_ADDRESS_ID   => :bind_id,
                num_N_OBJECT_ID        => :object_id,
                num_N_ADDRESS_ID       => :address_id,
                num_N_OBJ_ADDR_TYPE_ID => SYS_CONTEXT('CONST', 'BIND_ADDR_TYPE_Actual'),
                num_N_ADDR_STATE_ID    => SYS_CONTEXT('CONST', 'ADDR_STATE_On'),
                dt_D_END => SYSDATE
            );
        END;
    """

    _QUERY_GET_STB_ID_SERIAL_MAC = u"""
        WITH
            ud AS (select N_DEVICE_ID
                       from table(SI_USERS_PKG_S.GET_USER_DEVICES(:user_id))
                       where N_DEVICE_GOOD_ID = 50701401),
            dc AS (select * from SI_V_OBJECTS_SPEC_SIMPLE
                       where N_MAIN_OBJECT_ID in (select * from ud) and N_GOOD_ID = 50708501),
            ds AS (select N_OBJECT_ID, VC_SERIAL
                       from SI_V_DEVICES
                       where N_OBJECT_ID in (select * from ud)),
            ad AS (select * from SI_V_OBJ_ADDRESSES_SIMPLE a
                       where a.N_OBJECT_ID in (select dc.N_OBJECT_ID from dc) and a.N_ADDR_TYPE_ID=4006)
        select
            m.N_DEVICE_ID AS d_id,
            c.VC_CODE AS d_name,
            s.VC_SERIAL AS d_serial,
            c.N_OBJECT_ID AS c_id,
            c.VC_NAME AS c_name,
            a.VC_CODE AS c_mac
        from
            ud m left join
            dc c on m.N_DEVICE_ID = c.N_MAIN_OBJECT_ID left join
            ds s on m.N_DEVICE_ID = s.N_OBJECT_ID left join
            ad a on a.N_OBJECT_ID = c.N_OBJECT_ID
    """

    _QUERY_GET_ALL_SERVICES_ON_STB = u"""
            select N_GOOD_ID, VC_GOOD_NAME, VC_ACCOUNT, N_ACCOUNT_ID, N_OBJECT_ID from
            table(SI_USERS_PKG_S.USERS_CURRENT_SERVS_LIST(:user_id, 1))
            where N_OBJECT_ID in (%s)
            and N_DOC_STATE_ID = 4003
    """

    u"""
    Инициализирует сессию по паре 'имя пользователя'/'пароль'
    """
    _MAIN_INIT = u"""
        BEGIN
          MAIN.INIT(
             vch_VC_IP        => :ip,
             vch_VC_USER      => :user,
             vch_VC_PASS      => :password,
             vch_VC_APP_CODE  => 'NETSERV_ARM_Private_Office',
             vch_VC_CLN_APPID => 'portal');
        END;
    """

    _QUERY_GET_OFFICE_USER = u"""
        select N_SUBJECT_ID
        from SI_SUBJ_SERVICES
        where
            VC_LOGIN_REAL = :login and
            VC_PASS = :password and
            C_ACTIVE = 'Y' and
            N_SERVICE_ID = SYS_CONTEXT('CONST', 'NETSERV_ARM_Private_Office') and
            N_AUTH_TYPE_ID = SYS_CONTEXT('CONST','AUTH_TYPE_LOGINPASS')
    """

    u"""
    Получает список активных пакетов.
    SUB.N_SERVICE_ID      - ID услуги
    SUB.N_OBJECT_ID       - ID подписанного оборудования
    SUB.VC_SERVICE        - наименование услуги
    GS.VC_GOOD_TYPE_NAME  - тип услуги (услуга или пакет услуг)
    SS.VC_NAME            - полное наименование субъекта учёта
    DEND                  - дата окончания текущей услуги, если оно пустое,
                            то пользователю доступен только обязательный пакет.
    """
    _QUERY_GET_SUBSCRIPTIONS_AND_DATES = u"""
        select SUB.N_SERVICE_ID,
               SUB.N_OBJECT_ID,
               SUB.VC_SERVICE,
               GS.VC_GOOD_TYPE_NAME,
               SS.VC_NAME,
               TO_CHAR((select INV.D_END from SD_V_INVOICES_C INV
                          where
                              INV.N_DOC_ID=SUB.N_INVOICE_ID and
                              INV.D_END > SYSDATE and
                              INV.N_SERVICE_ID='1662333301'
                        ),'DD.MM.YYYY HH24:MI:SS') DEND
        from
            SI_V_SUBSCRIPTIONS     SUB,
            SR_V_GOODS_SIMPLE      GS,
            SI_V_SUBJ_ACCOUNTS     SACC,
            SI_V_SUBJECTS          SS
        where
            GS.N_GOOD_ID = SUB.N_SERVICE_ID and
            SUB.VC_ACCOUNT = :account and
            SACC.N_ACCOUNT_ID=SUB.N_ACCOUNT_ID and
            SS.N_SUBJECT_ID=SI_SUBJECTS_PKG_S.GET_BASE_SUBJECT_ID(SACC.N_SUBJECT_ID) and
            SUB.D_END IS NULL and
            GS.N_PARENT_GOOD_ID IN (12181237601, 50667201) and
            exists (select N_DOC_IDFROM SD_V_INVOICES_C CCC
                    where CCC.D_END > SYSDATE and
                          CCC.N_DOC_ID = SUB.N_INVOICE_ID and
                          CCC.N_SERVICE_ID='1662333301')
    """

    u"""
    Получает список активных пакетов.
    SUB.N_SERVICE_ID       - ID услуги
    GS.N_GOOD_ID 	       - ID услуги в номенклатуре
    SUB.N_PAR_SUBSCRIPTION_ID 	- ID родительской услуги
    SUB.N_DOC_ID		   - ID договора
    SUB.N_ACCOUNT_ID       - ID лицевого счета
    SUB.N_OBJECT_ID        - ID подписанного оборудования
    SUB.VC_SERVICE         - Наименование услуги
    SS.VC_NAME             - Полное наименование субъекта учёта
    """
    _QUERY_GET_SUBSCRIPTIONS = u"""
        select
            SUB.N_SERVICE_ID,
            GS.N_GOOD_ID,
            SUB.N_PAR_SUBSCRIPTION_ID,
            SUB.N_DOC_ID,
            SUB.N_ACCOUNT_ID,
            SUB.N_OBJECT_ID,
            SUB.VC_SERVICE,
            SS.VC_NAME,
            SS.N_SUBJECT_ID
        from
            SI_V_SUBSCRIPTIONS     SUB,
            SR_V_GOODS_SIMPLE      GS,
            SI_V_SUBJ_ACCOUNTS     SACC,
            SI_V_SUBJECTS          SS
        where
            GS.N_GOOD_ID = SUB.N_SERVICE_ID and
            SUB.VC_ACCOUNT= :account and
            SACC.N_ACCOUNT_ID=SUB.N_ACCOUNT_ID and
            SS.N_SUBJECT_ID=SI_SUBJECTS_PKG_S.GET_BASE_SUBJECT_ID(SACC.N_SUBJECT_ID) and
            SUB.D_END IS NULL and
            GS.N_PARENT_GOOD_ID IN (12181237601, 50667201) and
            exists (select N_DOC_IDFROM SD_V_INVOICES_C CCC
                    where CCC.D_END > SYSDATE and
                          CCC.N_DOC_ID = SUB.N_INVOICE_ID and
                          CCC.N_SERVICE_ID='1662333301')
    """

    u"""
    Перезаписывает подписки.
    num_N_PAR_SUBJ_GOOD_ID - идентификатор подписки на родительскую услугу.
    t_GOODS_LIST - идентификаторы услуг, которые должны быть подключены,
                   уже подключенные услуги, не входящие в список, отключаются.
    """
    _OVERWRITE_SUBSCRIPTIONS = u"""
    BEGIN
      AP_USER_OFFICE_PKG.PROCESS_ADD_GOODS(
        num_N_PAR_SUBJ_GOOD_ID => 10444710501,
        t_GOODS_LIST => AIS_NET.NUMBER_TABLE (%s)
      );
    END;
    """

    def __init__(self, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, db_name=DB_NAME):
        self._user = user
        self._password = password
        self._host = host
        self._db_name = db_name
        self._con = None
        self.connect()

    def connect(self):
        conn_str = "%s/%s@%s/%s" % (self._user, self._password, self._host, self._db_name)
        self._con = cx_Oracle.connect(conn_str)

    def close(self):
        try:
            self._con.close()
        except:
            pass

    def __del__(self):
        self.close()

    def __enter__(self):        
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def query(self, query, args):
        """
        Выполняет запрос и возвращает результат через fetchall
        """
        cur = self._con.cursor()
        cur.execute(query, args)
        out = cur.fetchall()
        cur.close()
        return out

    def query_wo_fetch(self, query, args):
        """
        Выполняет запрос и не возвращает результат
        """
        cur = self._con.cursor()
        cur.execute(query, args)
        cur.close()

    def call_function(self, function, return_type, args):
        """
        Выполняет функцию, возвращает результат.
        Требует ручного указания возвращаемого типа через параметр return_type.
        """
        cur = self._con.cursor()
        res = cur.callfunc(function, return_type, args)
        cur.close()
        return res

    def call_proc(self, function, args):
        cur = self._con.cursor()
        res = cur.callproc(function, args)
        cur.close()
        return res
    
    def get_user_by_login_pass(self, login, password):
        """
        Получет ID пользователя с заданным логином и паролем.
        Возвращет -1 если пользователь не найден.
        """
        args = {
            'login': login,
            'password': password,
        }
        result = self.query(HydraConnection._QUERY_GET_OFFICE_USER, args)
        if len(result) == 0:
            return -1
        return result[0][0]

    def main_init(self, user, password):
        """
        Инициализирует сессию.
        Необходимо выполнять данное действие перед выполнением функций и процедур,
        в противном случае возможна их некорректная работа.
        """
        args = {
            'ip': CURRENT_IP,
            'user': user,
            'password': password,
        }
        self.query_wo_fetch(HydraConnection._MAIN_INIT, args)

    def get_promised_payment(self, account):
        query = "select * from AP_V_PROMISED_PAYMENTS where N_ACCOUNT_ID = :account"
        args = {'account': account}
        result = self.query(query, args)
        return result

    def get_goods_and_dates(self, account):
        """
        Возвращает список кортежей с полями:
            0. ID услуги
            1. ID подписанного оборудования
            2. Наименование услуги
            3. Тип услуги (услуга или пакет услуг)
            4. ФИО пользователя
            5. дата окончания текущей услуги в формате 'DD.MM.YYYY HH24:MI:SS',
               если оно пустое, то пользователю доступен только обязательный пакет.
        """
        query = HydraConnection._QUERY_GET_SUBSCRIPTIONS_AND_DATES
        args = {'account': account}
        result = self.query(query, args)
        return result

    def get_goods(self, account):
        query = HydraConnection._QUERY_GET_SUBSCRIPTIONS
        args = {'account': account}
        result = self.query(query, args)
        return result

    def overwrite_subscriptions(self, account, tariffs):
        query = HydraConnection._OVERWRITE_SUBSCRIPTIONS % ','.join(tariffs)
        self.query_wo_fetch(query, {})

    def set_promised_payment(self, account_id):
        query = "begin\nAP_USER_OFFICE_PKG.SET_PROMISED_PAY(:account_id);\nend;"
        args = {
            'account_id': account_id,
        }
        self.query_wo_fetch(query, args)
        self.commit()

    def get_stb_list(self, user_id):
        """
        0. DEVICE_ID
        1. Имя устройства
        2. Серийный номер устройства
        3. OBJECTS_ID
        4.
        5. MAC-адрес
        """

        args = {'user_id': user_id}
        return self.query(HydraConnection._QUERY_GET_STB_ID_SERIAL_MAC, args)

    def get_all_services_on_stb(self, user_id, stb_list):
        objs = []
        for row in stb_list:
            if row[0]:  # DEVICE_ID
                objs.append(str(row[0]))
            if row[3]:  # OBJECTS_ID
                objs.append(str(row[3]))
        args = {
            'user_id': user_id,
        }

        return self.query(HydraConnection._QUERY_GET_ALL_SERVICES_ON_STB % ','.join(objs), args)

    def get_stb(self, user_id, mac, serial):
        stb_list = self.get_stb_list(user_id)
        service_list = self.get_all_services_on_stb(user_id, stb_list)
        for stb in stb_list:
            for service in service_list:
                if stb[2] is None and stb[5] is None and (stb[0] == service[4] or stb[3] == service[4]):
                    # serial is none, mac is none, not C_ID/D_ID == N_OBJECT_ID(port)
                    return stb
        return None
    
    def commit(self):
        try:
            self._con.commit()
        except:
            pass

    def set_mac_and_serial(self, user_id, mac, serial):
        stb = self.get_stb(user_id, mac, serial)
        if stb is None:
            raise HydraAdapterError(u"Все устройства уже зарегистрированы", 3)
        self._set_serial(stb[0], user_id, serial)  # stb[0] - device_id (D_ID)
        self._set_mac(mac, stb[3])  # stb[3] - port_id (C_ID)
        self.commit()

    def _set_serial(self, obj_id, owner_id, serial, firm_id=100, good_id=50701401):
        """
        Один тип приставки - 100
        """
        args = {
            'obj_id': obj_id,
            'owner_id': owner_id,
            'serial': serial,
            'firm_id': firm_id,
            'good_id': good_id,
        }
        q = HydraConnection._ADD_SERIAL
        self.query_wo_fetch(q, args)

    def _set_mac(self, mac, port_id):
        args = {
            'mac': mac,
            'port_id': port_id,
        }
        self.query_wo_fetch(HydraConnection._ADD_MAC, args)

    def get_all_services(self, user_id, account_id):
        query = """
            select VC_GOOD_NAME, N_SERVS_SUM 
            from table(SI_USERS_PKG_S.USERS_CURRENT_SERVS_LIST(:user_id)) 
            where N_ACCOUNT_ID = :account_id
        """
        args = {
            'account_id': account_id,
            'user_id': user_id,
        }
        return self.query(query, args)

    def get_account_by_ls(self, ls):
        """
        Запрашивает ID пользователя и ID аккаунта для лицевого счёта.
        Бросает исключаение с кодом 2 если лицевой счёт не найден.
        """
        query = "select N_ACCOUNT_ID, N_SUBJECT_ID from SI_V_SUBJ_ACCOUNTS where VC_CODE = :ls"
        args = {'ls': ls}
        result = self.query(query, args)
        if len(result) == 0:
            raise HydraAdapterError(u"Лицевой счёт не найден", 2)
        user_id = result[0][1]
        account_id = result[0][0]
        return user_id, account_id

    def set_mac_close_date(self, user_id, mac):
        stbs = self.get_stb_list(user_id)
        current_stb = None
        for stb in stbs:
            if stb[5] == mac:
                current_stb = stb
                break
        if current_stb is None:
            raise HydraAdapterError(u"MAC не найден", 4)
        
        object_id = current_stb[0]
        device_id = current_stb[3]

        query = """
            select N_OBJ_ADDRESS_ID,N_OBJECT_ID,N_ADDRESS_ID
            from SI_V_OBJ_ADDRESSES_SIMPLE
            where VC_CODE = :mac and (N_OBJECT_ID = :obj_id or N_OBJECT_ID = :dev_id)
        """
        args = {
            'mac': mac,
            'obj_id': object_id,
            'dev_id': device_id,
        }
        result = self.query(query, args)

        bind_id = result[0][0]
        object_id = result[0][1]
        address_id = result[0][2]
        args = {
            'bind_id': bind_id,
            'object_id': object_id,
            'address_id': address_id,
        }
        self.query_wo_fetch(HydraConnection._QUERY_CLOSE_MAC, args)
        self.commit()

    def get_balance(self, account):
        args = (account, datetime.datetime.now())
        function = "SI_USERS_PKG_S.GET_ACCOUNT_BALANCE_SUM"
        return_type = cx_Oracle.NUMBER
        return self.call_function(function, return_type, args)

    def get_recommended_pay(self, user_id):
        """
        Получает рекомендованный платёж для аккаунта
        """
        args = (user_id, )
        function = "SI_USERS_PKG_S.GET_USER_RECOMMENDED_PAY"
        return_type = cx_Oracle.NUMBER
        return self.call_function(function, return_type, args)

    def get_recommended_pay_list(self, account):
        query_str = "select * from table(SI_USERS_PKG_S.GET_RECOMMENDED_PAYMENT_LIST(:account))"
        args = {'account': account}
        result = self.query(query_str, args)
        return result

    def get_user_devices(self, user_id):
        query_str = "begin SI_USERS_PKG_S.GET_USER_DEVICES(:user_id); end;"
        args = {
            'user_id': user_id,
        }
        self.query(query_str, args)

    def accounts(self, maxrow):
        query_str = """select *
                from SI_V_SUBJ_ACCOUNTS
                where
                    N_ACCOUNT_TYPE_ID = SYS_CONTEXT('CONST', 'ACC_TYPE_Personal') and
                    ROWNUM <= :maxrow
        """
        args = {'maxrow': maxrow}
        result = self.query(query_str, args)
        return result

    def init_session(self, user_id, password=None, login=None):
        """
        Инициализируется сессию для пользователя user_id, запрашивает логин и пароль
        """
        if login is None or password is None:
            login, password = self.get_lk_login_pass(user_id)

        if login is None or password is None or len(login) == 0:
            raise HydraAdapterError(u'Ошибка авторизации', 7)

        self.main_init(login, password)

    def get_lk_login_pass(self, user_id):
        query_str = """
            select VC_LOGIN_REAL,VC_PASS
            from SI_SUBJ_SERVICES
            where
                C_ACTIVE = 'Y' and
                N_SERVICE_ID = SYS_CONTEXT('CONST', 'NETSERV_ARM_Private_Office') and
                N_SUBJECT_ID = :user_id
        """
        args = {'user_id': user_id}
        result = self.query(query_str, args)
        if len(result) == 0:
            raise HydraAdapterError(u'Пользователь не найден', 5)
        
        login = result[0][0]
        password = '' if result[0][1] is None else result[0][1]
        return unicode(login, "utf8"), unicode(password, "utf8")

    def get_active_billing_subscriptions(self, account_id):
        def check_date(good):
            # проверяем, что пакет ещё не истёк
            good_dt = datetime.datetime.strptime(good[5], '%d.%m.%Y %H:%M:%S')
            return good_dt > dt

        dt = datetime.datetime.now()
        return filter(check_date, self.get_goods_and_dates(account_id))

    def get_active_billing_packets(self, account_id):
        # Фильтруем по названию типа пакета
        packet_type = PACKET_TYPE_NAME
        return filter(lambda x: x[3] == packet_type, self.get_active_billing_packets(account_id))
