# -*- coding: utf-8 -*-
import os
import time

"""
Скрипт для очистки и оптимизации SQLite базы данных MicroPVR от устаревших записей
БД располагается в /etc/micropvr/

(c) Konstantin Shpinev, 2015
"""

now = int(time.time())
old_days = 15
print now

queries = []
def append_drop_table(tbl_name):
    global queries
    tbl_name = tbl_name.strip()
    queries.append("drop table `%s`" % tbl_name)

res = os.popen("sqlite3 records.db .tables").read()
tables = res.split('\n')
k = 0
for table in tables:
    try:
        mtime = table.split('time-')[1]
        mtime = int(mtime.split('_')[0])
        if (now - mtime)/60/60/24 > old_days:
            append_drop_table(table)
            k += 1
    except IndexError:
        pass

i = 0
query = ""
for q in queries:
    query += q + ";"
    i += 1
    if i >= 50:
        res = os.popen("sqlite3 records.db '%s'" % query).read()
        i = 0
        query = ""
        print res
if query:
    res = os.popen("sqlite3 records.db '%s'" % query).read()

res = os.popen("sqlite3 records.db vacuum").read()

print "clean done, dropped %d tables" % k
