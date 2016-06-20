# coding=utf-8
import os
import re
import config as config
import MySQLdb
from progress.bar import Bar
import sys
import re
import hashlib

"""
Скрипт миграции данных из БД OFT Middleware в БД Microimpuls Middleware
Дополнительно позволяет получить пароли пользователей в открытом виде из архива отправленных писем (EML)

(c) Konstantin Shpinev, 2015
"""

# Requirements:
# pip install mysqldb progress

# Connect to old OFT DB
oft_db = MySQLdb.connect(host=config.OFT_DB_HOST, user=config.OFT_DB_USER, passwd=config.OFT_DB_PASS, db=config.OFT_DB_NAME)
oft_cur = oft_db.cursor()

# Connect to new SMARTY DB
smarty_db = MySQLdb.connect(host=config.SMARTY_DB_HOST, user=config.SMARTY_DB_USER, passwd=config.SMARTY_DB_PASS, db=config.SMARTY_DB_NAME)
smarty_cur = smarty_db.cursor()

customers = {}
dealers = {}
passwords = {}
accounts_with_passwords_not_found = []


def clean_arr(arr):
    for k, v in arr.iteritems():
        if arr[k] == None or arr[k] == 'None':
            arr[k] = ""
        if arr[k] == "0000-00-00" or arr[k] == "0000-00-00 00:00:00":
            arr[k] = ""
    return arr


def clean_date(dt, not_null=False):
    if dt == "":
        if not_null:
            dt = "NOW()"
        else:
            dt = "NULL"
    else:
        dt = "'" + str(dt) + "'"
    return dt


def clean_int(s):
    if not s or s == "":
        return "NULL"
    si = ''.join(x for x in s if x.isdigit())
    if not si or si == "":
        return "NULL"
    return int(si)

def parse_passwords_from_eml():
    files = []
    for name in os.listdir(config.EML_PATH):
        if os.path.isfile(os.path.join(config.EML_PATH, name)):
            files.append(os.path.join(config.EML_PATH, name))
    l = {}
    for file_path in files:
        with open (file_path, "r") as f:
            data = f.read()
            b = re.search("base64", data)
            if b:
                data = data.replace('\n', '')
                b = re.search("base64(.+)--", data)
                if b:
                    data = b.groups()[0].decode('base64').strip()
            m = re.search("Логин: (\d+)</p>\s+<p>Пароль: (\d+)", data)
            if not m:
                m = re.search("Логин: (\d+)<br />Пароль: (\d+)", data)
            if not m:
                m = re.search("Логин: (\d+)\nПароль: (\d+)", data)
            if not m:
                m = re.search("Логин: (\d+)Пароль: (\d+)", data)
            if not m:
                m = re.search("Логин: (\d+)\s+Пароль: (\d+)", data)
            if m:
                m = m.groups()
                l[m[0]] = m[1]
            data = data.replace('\n', '')
            m = re.search("<p>Уважаемый/ая (.+) (.+)!.+Пароль: (\d+)", data)
            if m:
                m = m.groups()
                l[m[0]+"."+m[1]] = m[2]
    return l

def insert_contract(contract):
    contract = clean_arr(contract)
    if not contract['customer_id']:
        return None
    smarty_cur.execute("SELECT * FROM billing_contract WHERE number = '%s' AND customer_id = %d" %
        (contract['number'], contract['customer_id']))
    if smarty_cur.rowcount > 0:
        return None
    smarty_cur.execute("INSERT INTO billing_contract (number, created_at, customer_id) VALUES('%s', %s, %d)" %
        (contract['number'], clean_date(contract['created_at'], True), contract['customer_id']))
    smarty_db.commit()
    return smarty_cur.lastrowid

def insert_bank_account(bank_account):
    bank_account = clean_arr(bank_account)
    if not bank_account['customer_id']:
        return None
    smarty_cur.execute("SELECT * FROM billing_customerbankaccount WHERE number = '%s' AND customer_id = %d" %
        (bank_account['number'], bank_account['customer_id']))
    if smarty_cur.rowcount > 0:
        return None
    smarty_cur.execute("INSERT INTO billing_customerbankaccount (blz, bic, number, iban, bank_name, owner_name, customer_id) \
    VALUES('%s', '%s', '%s', '%s', '%s', '%s', %d)" %
    (bank_account['blz'], bank_account['bic'], bank_account['number'], bank_account['iban'],
    bank_account['bank_name'], bank_account['owner_name'], bank_account['customer_id']))
    smarty_db.commit()
    return smarty_cur.lastrowid

def insert_customer(customer):
    customer = clean_arr(customer)
    smarty_cur.execute("SELECT * FROM tvmiddleware_customer WHERE firstname = '%s' AND lastname = '%s'" %
        (customer['firstname'], customer['lastname']))
    if smarty_cur.rowcount > 0:
        return None
    postal_country = "NULL"
    billing_country = "NULL"
    if customer['postal_address_city'] != "":
        postal_country = config.COUNTRY_ID
    if customer['billing_address_city'] != "":
        billing_country = config.COUNTRY_ID
    dealer_id = "NULL"
    if customer['dealer_id'] != "":
        dealer_id = get_or_insert_dealer(dealers[customer['dealer_id']])
    if customer['postal_address_city'] == "":
        customer['postal_address_city'] = "NULL"
    if customer['billing_address_city'] == "":
        customer['billing_address_city'] = "NULL"
    if customer['postal_address_zip'] == "":
        customer['postal_address_zip'] = "NULL"
    if customer['billing_address_zip'] == "":
        customer['billing_address_zip'] = "NULL"
    if customer['gender'] == "":
        customer['gender'] = "NULL"
    else:
        customer['gender'] = int(customer['gender'])
    if customer['email'] == "":
        customer['email'] = "NULL"
    else:
        customer['email'] = "'" + customer['email'] + "'"
    sql = "INSERT INTO tvmiddleware_customer (firstname, lastname, birthdate, \
    postal_address_street, postal_address_zip, postal_address_name, postal_address_city_id, postal_address_country_id, \
    billing_address_street, billing_address_zip, billing_address_name, billing_address_city_id, billing_address_country_id, \
    phone_number_1, fax_phone_number, email, company_name, comment, client_id, dealer_id, gender, balance) \
    VALUES('%s', '%s', '%s', '%s', %s, '%s', %s, %s, '%s', %s, '%s', %s, %s, '%s', '%s', %s, '%s', '%s', %s, %s, %s, 0.0)" % \
    (customer['firstname'], customer['lastname'], customer['birthdate'], customer['postal_address_street'],
     clean_int(customer['postal_address_zip']), customer['postal_address_name'], customer['postal_address_city'], postal_country,
     customer['billing_address_street'], clean_int(customer['billing_address_zip']), customer['billing_address_name'],
     customer['billing_address_city'], billing_country, customer['phone_number_1'], customer['fax_phone_number'],
     customer['email'], customer['company_name'], customer['comment'], config.CLIENT_ID, dealer_id, customer['gender'])
    try:
        smarty_cur.execute(sql)
        smarty_db.commit()
        return smarty_cur.lastrowid
    except:
        print sql
        sys.exit()

def insert_account(account):
    account = clean_arr(account)
    smarty_cur.execute("SELECT * FROM tvmiddleware_account WHERE abonement = '%s' and client_id = %d" % (account['login'], config.CLIENT_ID))
    if smarty_cur.rowcount > 0:
        return None
    if len(account['login']) >= 11:
        return None
    if account['auto_activation_period'] == "":
        account['auto_activation_period'] = 0
    sql = "INSERT INTO tvmiddleware_account (abonement, `password`, active, activation_date, deactivation_date, \
    auto_activation_period, last_active, parent_code, created_at, ip, customer_id, client_id, allow_multiple_login) \
    VALUES('%s', '%s', %d, %s, %s, '%s', %s, '%s', %s, '%s', %s, %s, 0)" % \
    (account['login'], encode_password(account['password']), 1 if account['active'] else 0, clean_date(account['activation_date']),
     clean_date(account['deactivation_date']), account['auto_activation_period'], clean_date(account['last_active_date']), account['parent_code'],
     clean_date(account['created_at'], True), account['ip'], int(account['customer_id']), config.CLIENT_ID)
    try:
        smarty_cur.execute(sql)
        smarty_db.commit()
        return smarty_cur.lastrowid
    except:
        print sql
        sys.exit()

def insert_customer_to_tariff(tariff):
    if not tariff['customer_id']:
        return None
    if not tariff['tariff_id']:
        return None
    smarty_cur.execute("SELECT * FROM tvmiddleware_customer_tariffs WHERE customer_id = %d AND tariff_id = %d" %
        (int(tariff['customer_id']), int(tariff['tariff_id'])))
    if smarty_cur.rowcount > 0:
        return None
    sql = "INSERT INTO tvmiddleware_customer_tariffs (customer_id, tariff_id) VALUES(%d, %d)" % \
        (tariff['customer_id'], tariff['tariff_id'])
    smarty_cur.execute(sql)
    smarty_db.commit()

def get_or_insert_dealer(dealer):
    smarty_cur.execute("SELECT id FROM dealers_dealer WHERE lastname = '%s'" % dealer['lastname'])
    if smarty_cur.rowcount > 0:
        return smarty_cur.fetchone()[0]
    sql = "INSERT INTO dealers_dealer (lastname, billing_address_street, comment, client_id, email) \
    VALUES('%s', '%s', '%s', %d, NULL)" % (dealer['lastname'], dealer['billing_address_street'], dealer['comment'], config.CLIENT_ID)
    try:
        smarty_cur.execute(sql)
        smarty_db.commit()
        return smarty_cur.lastrowid
    except:
        print sql
        sys.exit()

def get_or_insert_city(name):
    if not name:
        return "NULL"
    smarty_cur.execute("SELECT id FROM geo_city WHERE name = '%s'" % name)
    if smarty_cur.rowcount > 0:
        return smarty_cur.fetchone()[0]
    smarty_cur.execute("INSERT INTO geo_city (name, country_id) VALUES('%s', %d)" % (name, config.COUNTRY_ID))
    smarty_db.commit()
    return smarty_cur.lastrowid

# Return new device_id related to oft stb_type_id
def map_device_id(id):
    try:
        return config.DEVICE_ID_MAP[str(id)]
    except:
        return None

# Return new tariff_id related to oft tarif_id
def map_tariff_id(id):
    try:
        return config.TARIFF_ID_MAP[str(id)]
    except:
        return None

def register_device(device):
    device = clean_arr(device)
    smarty_cur.execute("SELECT * FROM tvmiddleware_accountdevice WHERE device_uid = '%s'" % device['uid'])
    if smarty_cur.rowcount > 0:
        return None
    if not device['id'] or device['id'] == "":
        device['id'] = "NULL"
        return
    sql = "INSERT INTO tvmiddleware_accountdevice (device_uid, account_id, device_id, client_id, created_at) \
    VALUES('%s', %d, %s, %d, %s)" % (device['uid'], int(device['account_id']), device['id'], config.CLIENT_ID, clean_date(device['created_at'], True))
    smarty_cur.execute(sql)
    smarty_db.commit()

# Revert hash from MD5
def revert_hash(login, password, firstname, lastname):
    try:
        return passwords[login]
    except:
        try:
            return passwords["%s.%s" % (firstname, lastname)]
        except:
            if not login in accounts_with_passwords_not_found and len(str(login)) <= 10:
                accounts_with_passwords_not_found.append(login)
            return password

def encode_password(s):
    return hashlib.sha512(str(s)).hexdigest()

print "Parsing EMLs password base..."
passwords = parse_passwords_from_eml()
print "OK, %d passwords." % len(passwords)

print "Requesting customers..."
oft_cur.execute("SET NAMES utf8")
smarty_cur.execute("SET NAMES utf8")

# Get all customers from old db and save it into customers dict with key = old id
oft_cur.execute("SELECT \
    a.id, a.name, a.surname, a.birth_date, a.email, a.contract_number, a.active, a.gender, \
    a.organization, a.phone, a.fax, a.create_account, a.activate_date, a.deactivate_date, \
    a.comments, a.login_auto_activation_period, a.last_active_datetime, ai.street, ai.zip, \
    ai.city, ai.name, ai.surname, ab.blz, ab.konto, ab.bic, ab.iban, ab.bankName, ab.owner \
    FROM iptv_Accounts a \
    LEFT JOIN iptv_Account_Info ai ON (ai.account_id = a.id) \
    LEFT JOIN iptv_Accounts_BankAccount ab ON (ab.account_id = a.id) \
    GROUP BY ab.account_id \
    ORDER BY a.id ASC %s" % config.QUERY_CUSTOM_ENDING)
prev_id = None
for row in oft_cur.fetchall():
    id = row[0]
    firstname = row[1]
    lastname = row[2]
    birthdate = row[3]
    email = row[4]
    contract_number = row[5]
    account_active = row[6]
    gender = row[7]
    company_name = row[8]
    phone = row[9]
    fax = row[10]
    create_date = row[11]
    account_activation_date = row[12]
    account_deactivation_date = row[13]
    comment = row[14]
    account_auto_activation_period = row[15]
    account_last_active_date = row[16]
    street = row[17]
    zip = row[18]
    city = row[19]
    address_name = (row[20] + ' ' if row[20] else "") + (row[21] if row[21] else "")
    bank_blz = row[22]
    bank_number = row[23]
    bank_bic = row[24]
    bank_iban = row[25]
    bank_name = row[26]
    bank_owner = row[27]
    if email.find("@%s" % config.DOMAIN) != -1:
        email = ""
    if gender == 'male':
        gender = 0
    elif gender == 'female':
        gender = 1
    else:
        gender = ''
    if id == prev_id:
        customers[id]['postal_address_street'] = street
        customers[id]['postal_address_zip'] = zip
        customers[id]['postal_address_city'] = get_or_insert_city(city)
        customers[id]['postal_address_name'] = address_name

    if id != prev_id:
        customers[id] = {
            'customer_id': None,
            'firstname': firstname,
            'lastname': lastname,
            'birthdate': birthdate,
            'email': email,
            'gender': gender,
            'company_name': company_name,
            'phone_number_1': phone,
            'fax_phone_number': fax,
            'comment': comment,
            'postal_address_street': "",
            'postal_address_zip': "",
            'postal_address_city': "",
            'postal_address_name': "",
            'billing_address_street': street,
            'billing_address_zip': zip,
            'billing_address_city': get_or_insert_city(city),
            'billing_address_name': address_name,
            'account_active': account_active == "1",
            'account_activation_date': account_activation_date,
            'account_deactivation_date': account_deactivation_date,
            'account_auto_activation_period': account_auto_activation_period,
            'account_last_active_date': account_last_active_date,
            'account_created_at': create_date,
            'contract': {
                'number': contract_number,
                'created_at': create_date,
                'customer_id': None
            },
            'bank_account': {
                'blz': bank_blz,
                'bic': bank_bic,
                'number': bank_number,
                'iban': bank_iban,
                'bank_name': bank_name,
                'owner_name': bank_owner,
                'customer_id': None
            },
            'accounts': {},
            'dealer_id': None,
            'tariffs': []
        }
    prev_id = id

print "OK."
print "Requesting accounts..."

# Get all accounts for each customers, also get dealer
for id, customer in customers.iteritems():
    oft_cur.execute("SELECT \
    u.id, u.login, u.pass, u.ip_addr, u.channel_pass, s.mac, s.stb_type_id \
    FROM iptv_Users u \
    LEFT JOIN iptv_Stb s ON (s.id = u.stb_id) \
    WHERE u.account_id = %d" % id)
    prev_id = None
    for row in oft_cur.fetchall():
        account_id = row[0]
        login = row[1]
        password = row[2]
        ip = row[3]
        parent_code = row[4]
        device_uid = row[5]
        device_id = map_device_id(row[6])

        if prev_id == account_id:
            customer['accounts'][account_id]['devices'].append({
                'uid': device_uid,
                'id': device_id,
                'account_id': None,
                'created_at': customer['account_created_at']
            })
        if prev_id != account_id:
            customer['accounts'][account_id] = {
                'account_id': None,
                'customer_id': None,
                'login': login,
                'password': revert_hash(login, password, customer['firstname'], customer['lastname']),
                'ip': ip,
                'parent_code': revert_hash(login, parent_code, customer['firstname'], customer['lastname']),
                'active': customer['account_active'],
                'activation_date': customer['account_activation_date'],
                'deactivation_date': customer['account_deactivation_date'],
                'auto_activation_period': customer['account_auto_activation_period'],
                'last_active_date': customer['account_last_active_date'],
                'created_at': customer['account_created_at'],
                'devices': [{
                    'uid': device_uid,
                    'id': device_id,
                    'account_id': None,
                    'created_at': customer['account_created_at']
                }]
            }
        prev_id = account_id

    # Get dealer
    oft_cur.execute("SELECT * FROM iptv_Dealer_to_Accounts WHERE account_id = %d" % id)
    if oft_cur.rowcount > 0:
        row = oft_cur.fetchone()
        dealer_id = row[0]
        customer['dealer_id'] = dealer_id

print "OK."
print "Requesting dealers..."

# Get all dealers and their relations to customers
oft_cur.execute("SELECT \
    d.id, d.register, d.tax_number, d.value_added_tax_number, d.city, d.street, d.name \
    FROM iptv_Dealers d")
for row in oft_cur.fetchall():
    id = row[0]
    register = row[1]
    tax_number = row[2]
    value = row[3]
    city = row[4]
    street = row[5]
    name = row[6]
    comment = register + '\n' + tax_number + '\n' + value + '\n' + city
    dealers[id] = {
        'dealer_id': None,
        'lastname': name,
        'billing_address_street': street,
        'comment': comment
    }

print "OK."
print "Requesting tariff relations..."

# Get all customer to tariff relations
oft_cur.execute("SELECT at.account_id, at.tarif_id \
    FROM iptv_Account_to_Tariffs at")
for row in oft_cur.fetchall():
    id = row[0]
    tariff_id = row[1]
    if id not in customers:
        continue
    customers[id]['tariffs'].append({
        'customer_id': None,
        'tariff_id': map_tariff_id(tariff_id)
    })

print "OK."

# Let's go
# Insert all customers with all related items
bar = Bar('Migrating', max=len(customers))
for customer in customers.values():
    bar.next()

    id = insert_customer(customer)
    if id == None:
        continue
    customer['customer_id'] = id

    # Create contract
    customer['contract']['customer_id'] = customer['customer_id']
    id = insert_contract(customer['contract'])

    # Create bank account
    customer['bank_account']['customer_id'] = customer['customer_id']
    id = insert_bank_account(customer['bank_account'])

    # Create tariff relation
    for tariff in customer['tariffs']:
        tariff['customer_id'] = customer['customer_id']
        insert_customer_to_tariff(tariff)

    # Create accounts
    for account in customer['accounts'].values():
        account['customer_id'] = customer['customer_id']
        id = insert_account(account)
        if id == None:
            continue
        account['account_id'] = id

        # Create devices
        for device in account['devices']:
            device['account_id'] = account['account_id']
            register_device(device)

bar.finish()

print "Accounts without passwords: %d" % len(accounts_with_passwords_not_found)
for login in accounts_with_passwords_not_found:
    print login