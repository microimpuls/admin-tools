# -*- coding: utf-8 -*-

"""
Библиотека для вызова некоторых функций в системе Hydra напрямую через работу с СУБД
Использует cx_Oracle

(c) Alexander Larin, 2016
"""

import cx_Oracle
import codecs
import os
import datetime
os.environ["NLS_LANG"] = "Russian_Russia.UTF8"

USER = 'AIS_NET'
PASSWORD = 'pass'
HOST = 'example.com'
DBNAME = 'db'
IP = 'example.com'


class HydraAdapterError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class HydraConnection:

    _ADD_SERIAL = """
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

    _ADD_MAC = """
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

    _QUERY_CLOSE_MAC = """
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

    _QUERY_GET_STB_ID_SERIAL_MAC = """
        WITH
            ud AS (SELECT N_DEVICE_ID  FROM TABLE(SI_USERS_PKG_S.GET_USER_DEVICES(:user_id)) WHERE N_DEVICE_GOOD_ID = 50701401),
            dc AS (SELECT * FROM SI_V_OBJECTS_SPEC_SIMPLE WHERE N_MAIN_OBJECT_ID IN (SELECT * FROM ud) AND N_GOOD_ID = 50708501),
            ds AS (SELECT N_OBJECT_ID, VC_SERIAL FROM SI_V_DEVICES  WHERE N_OBJECT_ID IN (SELECT * FROM ud)),
            ad AS (SELECT * FROM SI_V_OBJ_ADDRESSES_SIMPLE a WHERE a.N_OBJECT_ID IN (SELECT dc.N_OBJECT_ID FROM dc) AND a.N_ADDR_TYPE_ID=4006)
        SELECT
            m.N_DEVICE_ID AS d_id,
            c.VC_CODE AS d_name,
            s.VC_SERIAL AS d_serial,
            c.N_OBJECT_ID AS c_id,
            c.VC_NAME AS c_name,
            a.VC_CODE AS c_mac
        FROM
            ud m LEFT JOIN
            dc c ON m.N_DEVICE_ID = c.N_MAIN_OBJECT_ID LEFT JOIN
            ds s ON m.N_DEVICE_ID = s.N_OBJECT_ID LEFT JOIN
            ad a ON a.N_OBJECT_ID = c.N_OBJECT_ID
    """

    _QUERY_GET_ALL_SERVS_ON_STB = """
            SELECT N_GOOD_ID,VC_GOOD_NAME, VC_ACCOUNT, N_ACCOUNT_ID, N_OBJECT_ID FROM
            TABLE(SI_USERS_PKG_S.USERS_CURRENT_SERVS_LIST(:user_id, 1))
            WHERE N_OBJECT_ID IN (%s)
            AND N_DOC_STATE_ID = 4003
    """
    
    _QUERY_MAIN_INIT = u"""
        BEGIN
          MAIN.INIT(
             vch_VC_IP        => :ip,
             vch_VC_USER      => :user,
             vch_VC_PASS      => :password,
             vch_VC_APP_CODE  => 'NETSERV_ARM_Private_Office',
             vch_VC_CLN_APPID => 'portal');
        END;
    """

    _QUERY_GET_OFFICE_USER = """
        SELECT N_SUBJECT_ID
        FROM SI_SUBJ_SERVICES
        WHERE
            VC_LOGIN_REAL = :login AND
            VC_PASS = :password AND
            C_ACTIVE = 'Y' AND
            N_SERVICE_ID = SYS_CONTEXT('CONST', 'NETSERV_ARM_Private_Office') AND
            N_AUTH_TYPE_ID = SYS_CONTEXT('CONST','AUTH_TYPE_LOGINPASS')
    """

    def __init__(self, user=USER, password=PASSWORD, host=HOST, db_name=DBNAME):
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
        cur = self._con.cursor()
        cur.execute(query, args)
        out = cur.fetchall()
        cur.close()
        return out

    def query_wo_fetch(self, query, args):
        cur = self._con.cursor()
        cur.execute(query, args)
        cur.close()

    def call_function(self, function, type, args):
        cur = self._con.cursor()
        res = cur.callfunc(function, type, args)
        cur.close()
        return res

    def call_proc(self, function, args):
        cur = self._con.cursor()
        res = cur.callproc(function, args)
        cur.close()
        return res
    
    def get_user_by_login_pass(self, login, password):
        args = {
            'login': login,
            'password': password,
        }
        result = self.query(HydraConnection._QUERY_GET_OFFICE_USER, args)
        if len(result) == 0:
            return -1
        return result[0][0]

    def main_init(self, user, password):
        args = {
            'ip': IP,
            'user': user,
            'password': password,
        }
        self.query_wo_fetch(HydraConnection._QUERY_MAIN_INIT, args)

    def get_promised_payment(self, account):
        query = "select * from AP_V_PROMISED_PAYMENTS where N_ACCOUNT_ID = :account"
        args = {'account': account}
        #args = {}
        #query_str = "select * from AP_V_PROMISED_PAYMENTS where ROWNUM < 1000"
        result = self.query(query, args)
        return result

    def set_promised_payment(self, account_id):
        # proc = "AP_USER_OFFICE_PKG.SET_PROMISED_PAY"
        # self.call_proc(proc, (account, ))
        query = "begin\nAP_USER_OFFICE_PKG.SET_PROMISED_PAY(:account_id);\nend;"
        args = {
            'account_id': account_id,
        }
        self.query_wo_fetch(query, args)
        self.commit()

    def get_stb_id_seral_mac(self, user_id):
        args = {'user_id': user_id}
        return self.query(HydraConnection._QUERY_GET_STB_ID_SERIAL_MAC, args)

    def get_all_servs_on_stb(self, user_id, stb_list):
        # result = self.get_stb_id_seral_mac(user_id)
        objs = []
        for row in stb_list:
            if row[0]:  # DEVICE_ID
                objs.append(str(row[0]))
            if row[3]:  # OBJECTS_ID
                objs.append(str(row[3]))
        args = {
            'user_id': user_id,
        }

        return self.query(HydraConnection._QUERY_GET_ALL_SERVS_ON_STB % ','.join(objs), args)

    def get_stb(self, user_id, mac, serial):
        stb_list = self.get_stb_id_seral_mac(user_id)
        servs_list = self.get_all_servs_on_stb(user_id, stb_list)
        for stb in stb_list:
            for serv in servs_list:
                if stb[2] is None and stb[5] is None and (stb[0] == serv[4] or stb[3] == serv[4]):
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
        self._set_serial(stb[0], user_id, serial)  # stb0 - device_id (D_ID)
        self._set_mac(mac, stb[3])  # stb3 - port_id (C_ID)
        self.commit()

    def _set_serial(self, obj_id, owner_id, serial, firm_id=100, good_id=50701401):
        args = {
            'obj_id': obj_id,
            'owner_id': owner_id,
            'serial': serial,
            'firm_id': firm_id,
            'good_id': good_id,
        }
        #args = {}
        q = HydraConnection._ADD_SERIAL# % (obj_id, good_id, serial, firm_id, owner_id)
        self.query_wo_fetch(q, args)

    def _set_mac(self, mac, port_id):
        args = {
            'mac': mac,
            'port_id': port_id,
        }
        self.query_wo_fetch(HydraConnection._ADD_MAC, args)

    def get_all_servs(self, user_id, account_id):
        # query = "SELECT * FROM TABLE(SI_USERS_PKG_S.USERS_CURRENT_SERVS_LIST(:user_id,1))"
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
        query = "select N_ACCOUNT_ID, N_SUBJECT_ID from SI_V_SUBJ_ACCOUNTS where VC_CODE = :ls"
        args = {'ls': ls}
        result = self.query(query, args)
        if len(result) == 0:
            raise HydraAdapterError(u"Лицевой счёт не найден", 2)
        return result[0][1], result[0][0]

    def set_mac_close_date(self, user_id, mac):
        stbs = self.get_stb_id_seral_mac(user_id)
        current_stb = None
        for stb in stbs:
            if stb[5] == mac:
                current_stb = stb
                break
        if current_stb is None:
            raise HydraAdapterError(u"MAC не найден", 4)
        
        object_id = current_stb[0]
        device_id = current_stb[3]

        query = "select N_OBJ_ADDRESS_ID,N_OBJECT_ID,N_ADDRESS_ID from SI_V_OBJ_ADDRESSES_SIMPLE where VC_CODE = :mac and (N_OBJECT_ID = :obj_id or N_OBJECT_ID = :dev_id)"
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
        type = cx_Oracle.NUMBER
        return self.call_function(function, type, args)

    def get_recommended_pay(self, user_id):
        args = (user_id, )
        function = "SI_USERS_PKG_S.GET_USER_RECOMMENDED_PAY"
        type = cx_Oracle.NUMBER
        return self.call_function(function, type, args)

    def get_recommended_pay_list(self, account):
        query_str = "SELECT * FROM table(SI_USERS_PKG_S.GET_RECOMMENDED_PAYMENT_LIST(:account))"
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
        query_str = "SELECT * FROM   SI_V_SUBJ_ACCOUNTS WHERE  N_ACCOUNT_TYPE_ID = SYS_CONTEXT('CONST', 'ACC_TYPE_Personal')" \
                    "and ROWNUM <= :maxrow"
        args = {'maxrow': maxrow}
        result = self.query(query_str, args)
        return result

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

    @staticmethod
    def fine_print(toprint):
        for result in toprint:
            for e in result:
                c = unicode(str(e), "utf8")
                print c,
            print

 
