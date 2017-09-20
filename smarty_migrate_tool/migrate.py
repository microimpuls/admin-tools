# -*- coding: utf-8 -*-
import os
import config as config
import MySQLdb
import tables

# Requirements:
# pip install mysqldb

# Connect one
from_db = MySQLdb.connect(host=config.FROM_DB_HOST, user=config.FROM_DB_USER,
                          passwd=config.FROM_DB_PASS, db=config.FROM_DB_NAME)
from_cur = from_db.cursor()

# Connect two
to_db = MySQLdb.connect(host=config.TO_DB_HOST, user=config.TO_DB_USER,
                        passwd=config.TO_DB_PASS, db=config.TO_DB_NAME)
to_cur = to_db.cursor()
# smarty_cur = None

print "Building database structure..."
tables_temps = tables.get_tables(to_cur)
print "OK"

client_id = -1


def parse_result(row, args):
    out = dict()
    for i in range(len(args)):
        out[args[i][0]] = row[i]
    return out


def get_client(r_client_id):
    tmpl = tables_temps['clients_client']
    sql = tmpl.select + " WHERE id = %s" % r_client_id
    print sql
    from_cur.execute(sql)
    if from_cur.rowcount > 1:
        print("More than one client was found")
        return None
    if from_cur.rowcount == 0:
        print("Client is not found")
        return None
    row = from_cur.fetchone()
    client = parse_result(row, tmpl.fields)
    return client


def set_client(client):
    tmpl = tables_temps['clients_client']

    sql = tmpl.insert + "("
    for field in tmpl.fields:
        if client[field[0]] == None:
            client[field[0]] = 'NULL'
        # if field[0] == 'id':
        #    continue
        if field[1] == 1:
            sql += "'%s', " % client[field[0]]
        else:
            sql += "%s, " % client[field[0]]

    sql = sql[:-2] + ")"
    print sql
    to_cur.execute(sql)
    to_db.commit()
    return to_cur.lastrowid


def get_by_list(table, crit, value_list, id_arr):
    print "Select %s..." % table,
    out = []
    tmpl = tables_temps[table]
    for value in value_list:
        from_cur.execute(tmpl.select + " WHERE %s=%d" % (crit, value[id_arr]))
        out += to_list(from_cur.fetchall())
    print "OK"
    return out


def get_by(table, crit, value):
    print "Select %s..." % table,
    tmpl = tables_temps[table]
    sql = tmpl.select + " WHERE %s=%d" % (crit, value)
    from_cur.execute(sql)
    out = from_cur.fetchall()
    print "OK"
    return out


def get_all(table):
    print "Select %s..." % table,
    tmpl = tables_temps[table]
    from_cur.execute(tmpl.select)
    out = from_cur.fetchall()
    print "OK"
    return out


def clear_value(value, descr):

    if value is None:
        return "NULL, "
    if descr[1] == 1:
        return "'%s', " % value.replace("'", "\\'")
    if descr[1] == 2:
        return "%d, " % value
    if descr[1] == 3 or descr[1] == 4:
        return "'%s', " % value.isoformat()
    if descr[1] == 5 or descr[1] == 0:
        return "%f, " % value

    raise TypeError("Unknown SQL type")


def insert_one(tmpl, to_insert):
    #### if exists
    # sql_r = "select %s.id from %s where is=%d" % (tmpl.name, tmpl.name, to_insert[0])
    # to_cur.execute(sql_r)
    # if to_cur.rowcount > 0:
    #   return to_insert[0]
    sql = tmpl.insert + '('
    for i in xrange(0, len(tmpl.fields)):
        sql += clear_value(to_insert[i], tmpl.fields[i])
    sql = sql[:-2] + ')'
    try:
        print sql
        to_cur.execute(sql)
    except MySQLdb.ProgrammingError as l:
        print sql
        print l.message
        exit(0)
    # to_db.commit()

    return to_cur.lastrowid


def insert(table, to_insert):
    tmpl = tables_temps[table]
    print "insert %s, %d rows..." % (table, len(to_insert))
    out = dict()
    for row in to_insert:
        new_id = insert_one(tmpl, row)
        out[row[0]] = new_id
    print "OK"
    to_db.commit()
    return out


def check_name(table, name):
    sql = "select %s.id from %s where %s.name='%s'" % (table.name, table.name, table.name, name)
    to_cur.execute(sql)
    if to_cur.rowcount > 0:
        return from_cur.fetchone()[0]
    return -1


def insert_with_check_name(table, to_insert):
    tmpl = tables_temps[table]
    out = dict()
    name_col = tmpl.field_id('name')

    for row in to_insert:
        old_id = check_name(tmpl, row[name_col])
        if old_id >= 0:
            out[row[0]] = old_id
        else:
            new_id = insert_one(tmpl, row)
            out[row[0]] = new_id
    return out


def to_list(tuple):
    out = []
    for t in tuple:
        out.append(list(t))
    return out


def replace_id(table, field, new_id, to_replace):
    tmpl = tables_temps[table]
    c_id = tmpl.field_id(field)
    for r in to_replace:
        if r[c_id] is None:
            continue
        r[c_id] = new_id


def replace_many_ids(table, field, new_ids, to_replace):
    tmpl = tables_temps[table]
    c_id = tmpl.field_id(field)
    for r in to_replace:
        if r[c_id] is None:
            continue
        r[c_id] = new_ids[r[c_id]]


def clear_icon_url():
    sql = "UPDATE tvmiddleware_epgchannel SET " \
          "tvmiddleware_epgchannel.icon_url = " \
          "REPLACE(tvmiddleware_epgchannel.icon_url, 'http://smarty.microimpuls.com/',  '/');"

    to_cur.execute(sql)
    to_db.commit()
