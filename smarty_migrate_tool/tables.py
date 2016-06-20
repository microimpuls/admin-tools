def gen_select_template(args, table_name):
    temp = "SELECT "
    for arg in args:
        temp += "%s.%s, " % (table_name, arg[0])
    temp = temp[:-2] + " FROM " + table_name
    return temp


def gen_insert_template(args, table_name):
    temp = "INSERT INTO %s (" % table_name

    temp_args = args#[1:]  # w/o id

    for arg in temp_args:
        temp += "%s.%s, " % (table_name, arg[0])
    temp = temp[:len(temp) - 2] + ") VALUES "
    # temp = temp[:len(temp) - 1] + ") VALUES ("
    # for arg in temp_args:
    #     if arg[1]:
    #         temp += "'%s',"
    #     else:
    #         temp += "%d,"
    # temp = temp[:len(temp) - 1] + ")"
    return temp


def gen_table(table_name, cursor):
    cursor.execute("select column_name, column_type from information_schema.columns where table_name = '%s';"
                   % table_name)

    columns = []
    for row in cursor.fetchall():
        column_name = row[0]
        column_type = row[1]
        if 'text' in column_type or 'char' in column_type:
            type = 1
        elif 'int' in column_type:
            type = 2
        elif 'datetime' in column_type:
            type = 3
        elif 'date' in column_type:
            type = 4
        elif 'decimal' in column_type:
            type = 5
        else:
            type = 0
        columns.append((column_name, type))

    return Table(columns, table_name)


class Table:
    def __init__(self, fields, name):
        self.fields = fields
        self.name = name
        self.select = gen_select_template(fields, name)
        self.insert = gen_insert_template(fields, name)

    def field_id(self, name):
        for i in range(len(self.fields)):
            if self.fields[i][0] == name:
                return i
        return -1


tables_list = [
    'auth_group',
    'auth_group_permissions',
    'auth_permission',
    'auth_user',
    'auth_user_groups',
    'auth_user_user_permissions',
    'billing_contract',
    'billing_customerbankaccount',
    'billing_customertransaction',
    'billing_document',
    'billing_documenttemplate',
    'billing_invoice',
    'billing_invoiceitem',
    'billing_paypalmerchantdata',
    'billing_product',
    'billing_w1cardmerchantdata',
    'billing_w1merchantdata',
    'captcha_captchastore',
    'clients_client',
    'dealers_dealer',
    'django_admin_log',
    'django_content_type',
    'django_geoip_city',
    'django_geoip_country',
    'django_geoip_iprange',
    'django_geoip_region',
    'django_migrations',
    'django_session',
    'django_site',
    'geo_city',
    'geo_country',
    'geo_ip2locationcity',
    'geo_ip2locationcountry',
    'monitoring_clientevent',
    'monitoring_clientevent_action_contacts',
    'monitoring_clientevent_streams',
    'monitoring_clienteventcontact',
    'monitoring_event',
    'monitoring_host',
    'monitoring_stream',
    'monitoring_streamcheck',
    'monitoring_streamgroup',
    'tvmiddleware_account',
    'tvmiddleware_accountauthkey',
    'tvmiddleware_accountchannel',
    'tvmiddleware_accountdevice',
    'tvmiddleware_accountgamerecord',
    'tvmiddleware_casservice',
    'tvmiddleware_casservice_devices',
    'tvmiddleware_category',
    'tvmiddleware_channel',
    'tvmiddleware_channel_stream_services',
    'tvmiddleware_channel_tariffs',
    'tvmiddleware_channeliconsize',
    'tvmiddleware_clientplaydevice',
    'tvmiddleware_customer',
    'tvmiddleware_customer_tariffs',
    'tvmiddleware_datacenter',
    'tvmiddleware_epg',
    'tvmiddleware_epgcategory',
    'tvmiddleware_epgchannel',
    'tvmiddleware_epgsource',
    'tvmiddleware_epgsourcecategorymap',
    'tvmiddleware_externalapplication',
    'tvmiddleware_externalapplication_devices',
    'tvmiddleware_game',
    'tvmiddleware_game_clients',
    'tvmiddleware_genre',
    'tvmiddleware_maintenance',
    'tvmiddleware_maintenance_channels',
    'tvmiddleware_maintenance_stream_services',
    'tvmiddleware_message',
    'tvmiddleware_npvrtasks',
    'tvmiddleware_playdevice',
    'tvmiddleware_playdevicetemplate',
    'tvmiddleware_radio',
    'tvmiddleware_radio_tariffs',
    'tvmiddleware_streamservice',
    'tvmiddleware_streamservice_cas_service',
    'tvmiddleware_tariff',
    'tvmiddleware_tariff_available_in_cities',
    'tvmiddleware_tariff_available_in_countries',
    'tvmiddleware_tariff_stream_services',
    'tvmiddleware_video',
    'tvmiddleware_video_genres',
    'tvmiddleware_video_stream_services',
    'tvmiddleware_video_tariffs',
    'tvmiddleware_videofile',
    'widgets_widget',
    'widgets_widgetproperty',
    'widgets_widgettoken',
]


def get_tables(cursor):
    tables_templ = dict()

    for table in tables_list:
        tables_templ[table] = gen_table(table, cursor)
    return tables_templ
