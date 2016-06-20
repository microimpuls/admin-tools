def get_all_tables(cursor):
    cursor.execute("show tables;")

    a = cursor.fetchall()
    output = open('output', 'w')
    output.write('[\n')
    for row in a:
        output.write("['%s', " % row)
        cursor.execute("select column_name, column_type from information_schema.columns where table_name = '%s';" % row)
        cols = cursor.fetchall()
        all = ''
        has_client_id = False
        for col in cols:
            if '_id' in col[0]:
                if col[0] == 'client_id':
                    has_client_id = True
                else:
                    if len(all) > 0:
                        all += ', '
                    all += "'%s'" % col[0]
        if has_client_id:
            output.write("'client_id', True, ")
        else:
            output.write("'', False, ")
        output.write('[%s]],\n' % all)
    output.write(']')
    output.close()


def gen_functions(inp):
    """
    ['table_name', 'filter_id', True, ['filter_id', 'filter2_id']]

    Example:
    inp = [
        ['django_content_type', '', False, []],
        ['django_geoip_country', '', False, []],
        ['django_geoip_region', '', False, ['country_id']],
        ['django_geoip_city', '', False, ['region_id']],
        ['django_geoip_iprange', '', False, ['city_id', 'country_id', 'region_id']],
    ]

    """
    for i in inp:
        table = i[0]
        get_by = i[1]
        replace_client = i[2]
        replace_many_ids = i[3]

        name = table[table.find('_') + 1:]

        if get_by == '':
            print "%s = get_all('%s')" % (name, table)
        elif get_by == 'client_id':
            print "%s = to_list(get_by('%s', 'client_id', client_id))" % (name, table)
        else:
            print "%s = to_list(get_by_list('%s', '%s', %s))" % (name, table, get_by, get_by[:-3])

        if replace_client:
            print "replace_id('%s', 'client_id', new_client_id, %s)" % (table, name)

        for t in replace_many_ids:
            print "replace_many_ids('%s', '%s', %s, %s)" % (table, t, t + '_map', name)

        print "%s = insert('%s', %s)\n" % (name + '_id_map', table, name)
