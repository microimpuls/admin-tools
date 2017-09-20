# -*- coding: utf-8 -*-

"""
Скрипт миграции данных по конкретному client_id из одной БД Smarty в другую БД Smarty

(c) Alexander Larin, 2016
"""

from migrate import *

from_cur.execute("SET NAMES utf8")
to_cur.execute("SET NAMES utf8")

print "Check client..."
client = get_client(config.CLIENT_ID)
client_id = client['id']
print "Client ID: %d" % client['id']
#new_client_id = 93

new_client_id = set_client(client)
print "Ok..."

# Common tables
# EPG
## ATTENTION! Code below was generated.

print "Copy EPG"

cat = get_all('tvmiddleware_epgcategory')
source = get_all('tvmiddleware_epgsource')
source_cat = to_list(get_all('tvmiddleware_epgsourcecategorymap'))
# epg = to_list(get_all('tvmiddleware_epg'))
epg_channel = to_list(get_all('tvmiddleware_epgchannel'))

cat_id_map = insert('tvmiddleware_epgcategory', cat)
source_id_map = insert('tvmiddleware_epgsource', source)

# replace_many_ids('tvmiddleware_epgsourcecategorymap', 'epg_category_id', cat_id_map, source_cat)
# replace_many_ids('tvmiddleware_epgsourcecategorymap', 'epg_source_id', source_id_map, source_cat)
# replace_many_ids('tvmiddleware_epgchannel', 'epg_source_id', source_id_map, epg_channel)

epg_channel_id_map = insert('tvmiddleware_epgchannel', epg_channel)
insert('tvmiddleware_epgsourcecategorymap', source_cat)
clear_icon_url()

# # replace_many_ids('tvmiddleware_epg', 'epg_channel_id', epg_channel_id_map, epg)
# # replace_many_ids('tvmiddleware_epg', 'epg_category_id', cat_id_map, epg)
# epg_id_map = insert('tvmiddleware_epg', epg)

# GAME
print "Copy game"

game = get_all('tvmiddleware_game')
game_id_map = insert('tvmiddleware_game', game)

game_clients = to_list(get_by('tvmiddleware_game_clients', 'client_id', client_id))
# replace_many_ids('tvmiddleware_game_clients', 'game_id', game_id_map, game_clients)
replace_id('tvmiddleware_game_clients', 'client_id', new_client_id, game_clients)
insert('tvmiddleware_game_clients', game_clients)

# DEVICES
print "Copy devices"

play = get_all('tvmiddleware_playdevice')
play_id_map = insert('tvmiddleware_playdevice', play)

template = get_all('tvmiddleware_playdevicetemplate')
template_id_map = insert('tvmiddleware_playdevicetemplate', template)

cpd = to_list(get_by('tvmiddleware_clientplaydevice', 'client_id', client_id))
replace_id('tvmiddleware_clientplaydevice', 'client_id', new_client_id, cpd)
# replace_many_ids('tvmiddleware_clientplaydevice', 'play_device_id', play_id_map, cpd)
# replace_many_ids('tvmiddleware_clientplaydevice', 'template_id', template_id_map, cpd)
clientplaydevice_id_map = insert('tvmiddleware_clientplaydevice', cpd)

# DEALERS
print "Copy dealers"

dealers = to_list(get_by('dealers_dealer', 'client_id', client_id))
replace_id('dealers_dealer', 'client_id', new_client_id, dealers)
dealer_id_map = insert('dealers_dealer', dealers)

# GEO
print "Copy geo"

# geo_country = get_all('geo_country')
# geo_city = to_list(get_all('geo_city'))
# geo_ip2country = get_all('geo_ip2locationcountry')
# geo_ip2city = get_all('geo_ip2locationcity')

# country_id_map = insert('geo_country', geo_country)
# replace_many_ids('geo_city', 'country_id', country_id_map, geo_city)

# ip2country_id_map = insert('geo_ip2locationcountry', geo_ip2country)
# ip2city_id_map = insert('geo_ip2locationcity', geo_ip2city)
# city_id_map = insert('geo_city', geo_city)


# DATACENTER
print "Copy dc"

datacenter = to_list(get_by('tvmiddleware_datacenter', 'client_id', client_id))
replace_id('tvmiddleware_datacenter', 'client_id', new_client_id, datacenter)
datacenter_id_map = insert('tvmiddleware_datacenter', datacenter)

# STREAMSERVICE
print "Copy SS"

streamservice = to_list(get_by('tvmiddleware_streamservice', 'client_id', client_id))

#streamservice_cas_service = get_by_list('tvmiddleware_streamservice_cas_service', 'streamservice_id', streamservice, 0)

replace_id('tvmiddleware_streamservice', 'client_id', new_client_id, streamservice)
streamservice_id_map = insert('tvmiddleware_streamservice', streamservice)

# replace_many_ids('tvmiddleware_streamservice_cas_service', 'streamservice_id', streamservice_id_map, streamservice_cas_service)
# replace_many_ids('tvmiddleware_streamservice_cas_service', 'casservice_id', casservice_id_map, streamservice_cas_service)
#insert('tvmiddleware_streamservice_cas_service', streamservice_cas_service)

# TARIFF
print "Copy tariff"

tariff = to_list(get_by('tvmiddleware_tariff', 'client_id', client_id))
tariff_available_in_cities = get_by_list('tvmiddleware_tariff_available_in_cities', 'tariff_id', tariff, 0)
tariff_available_in_countries = get_by_list('tvmiddleware_tariff_available_in_countries', 'tariff_id', tariff, 0)
tariff_stream_services = get_by_list('tvmiddleware_tariff_stream_services', 'tariff_id', tariff, 0)

replace_id('tvmiddleware_tariff', 'client_id', new_client_id, tariff)
tariff_id_map = insert('tvmiddleware_tariff', tariff)

# replace_many_ids('tvmiddleware_tariff_available_in_cities', 'tariff_id', tariff_id_map, tariff_available_in_cities)
# replace_many_ids('tvmiddleware_tariff_available_in_cities', 'city_id', city_id_map, tariff_available_in_cities)

# replace_many_ids('tvmiddleware_tariff_available_in_countries', 'tariff_id', tariff_id_map, tariff_available_in_countries)
# replace_many_ids('tvmiddleware_tariff_available_in_countries', 'countries_id', country_id_map, tariff_available_in_countries)

# replace_many_ids('tvmiddleware_tariff_stream_services', 'tariff_id', tariff_id_map, tariff_stream_services)
# replace_many_ids('tvmiddleware_tariff_stream_services', 'streamservices_id', streamservice_id_map, tariff_stream_services)
insert('tvmiddleware_tariff_stream_services', tariff_stream_services)
insert('tvmiddleware_tariff_available_in_countries', tariff_available_in_countries)
insert('tvmiddleware_tariff_available_in_cities', tariff_available_in_cities)

# CHANNELS
print "Copy channels"

category = to_list(get_by('tvmiddleware_category', 'client_id', client_id))
replace_id('tvmiddleware_category', 'client_id', new_client_id, category)
category_id_map = insert('tvmiddleware_category', category)

channel = to_list(get_by('tvmiddleware_channel', 'client_id', client_id))
replace_id('tvmiddleware_channel', 'client_id', new_client_id, channel)
# replace_many_ids('tvmiddleware_channel', 'category_id', category_id_map, channel)
# replace_many_ids('tvmiddleware_channel', 'epg_channel_id', epg_channel_id_map, channel)
channel_id_map = insert('tvmiddleware_channel', channel)

channel_stream_services = to_list(get_by_list('tvmiddleware_channel_stream_services', 'channel_id', channel, 0))
# replace_many_ids('tvmiddleware_channel_stream_services', 'channel_id', channel_id_map, channel_stream_services)
# replace_many_ids('tvmiddleware_channel_stream_services', 'streamservice_id', streamservice_id_map, channel_stream_services)
channel_stream_services_id_map = insert('tvmiddleware_channel_stream_services', channel_stream_services)

channel_tariffs = to_list(get_by_list('tvmiddleware_channel_tariffs', 'channel_id', channel, 0))
# replace_many_ids('tvmiddleware_channel_tariffs', 'channel_id', channel_id_map, channel_tariffs)
# replace_many_ids('tvmiddleware_channel_tariffs', 'tariff_id', tariff_id_map, channel_tariffs)
hannel_tariffs_id_map = insert('tvmiddleware_channel_tariffs', channel_tariffs)

channeliconsize = to_list(get_by('tvmiddleware_channeliconsize', 'client_id', client_id))
replace_id('tvmiddleware_channeliconsize', 'client_id', new_client_id, channeliconsize)
channeliconsize_id_map = insert('tvmiddleware_channeliconsize', channeliconsize)

# CUSTOMER
print "Copy customers"

customer = to_list(get_by('tvmiddleware_customer', 'client_id', client_id))

replace_id('tvmiddleware_customer', 'client_id', new_client_id, customer)
# replace_many_ids('tvmiddleware_customer', 'billing_address_city_id', city_id_map, customer)
# replace_many_ids('tvmiddleware_customer', 'billing_address_country_id', country_id_map, customer)
# replace_many_ids('tvmiddleware_customer', 'postal_address_city_id', city_id_map, customer)
# replace_many_ids('tvmiddleware_customer', 'postal_address_country_id', country_id_map, customer)
# replace_many_ids('tvmiddleware_customer', 'dealer_id', dealer_id_map, customer)
customer_id_map = insert('tvmiddleware_customer', customer)

customer_tariffs = to_list(get_by_list('tvmiddleware_customer_tariffs', 'customer_id', customer, 0))
# replace_many_ids('tvmiddleware_customer_tariffs', 'customer_id', customer_id_map, customer_tariffs)
# replace_many_ids('tvmiddleware_customer_tariffs', 'tariff_id', tariff_id_map, customer_tariffs)
customer_tariffs_id_map = insert('tvmiddleware_customer_tariffs', customer_tariffs)

# externalapplication
print "Copy external"

externalapplication = to_list(get_by('tvmiddleware_externalapplication', 'client_id', client_id))
replace_id('tvmiddleware_externalapplication', 'client_id', new_client_id, externalapplication)
externalapplication_id_map = insert('tvmiddleware_externalapplication', externalapplication)

externalapplication_devices = to_list(get_by_list('tvmiddleware_externalapplication_devices', 'externalapplication_id', externalapplication, 0))
# replace_many_ids('tvmiddleware_externalapplication_devices', 'externalapplication_id', externalapplication_id_map, externalapplication_devices)
# replace_many_ids('tvmiddleware_externalapplication_devices', 'clientplaydevice_id', clientplaydevice_id_map, externalapplication_devices)
externalapplication_devices_id_map = insert('tvmiddleware_externalapplication_devices', externalapplication_devices)

# GENRE
print "Copy genre"

genre = to_list(get_by('tvmiddleware_genre', 'client_id', client_id))
replace_id('tvmiddleware_genre', 'client_id', new_client_id, genre)
genre_id_map = insert('tvmiddleware_genre', genre)

# RADIO
print "Copy radio"

radio = to_list(get_by('tvmiddleware_radio', 'client_id', client_id))
replace_id('tvmiddleware_radio', 'client_id', new_client_id, radio)
radio_id_map = insert('tvmiddleware_radio', radio)

# TV MIDDLEWARE
print "Copy tariffs"

radio_tariffs = to_list(get_by_list('tvmiddleware_radio_tariffs', 'radio_id', radio, 0))
# replace_many_ids('tvmiddleware_radio_tariffs', 'radio_id', radio_id_map, radio_tariffs)
# replace_many_ids('tvmiddleware_radio_tariffs', 'tariff_id', tariff_id_map, radio_tariffs)
radio_tariffs_id_map = insert('tvmiddleware_radio_tariffs', radio_tariffs)

print "Copy video"

video = to_list(get_by('tvmiddleware_video', 'client_id', client_id))
replace_id('tvmiddleware_video', 'client_id', new_client_id, video)
video_id_map = insert('tvmiddleware_video', video)

video_genres = to_list(get_by_list('tvmiddleware_video_genres', 'video_id', video, 0))
# replace_many_ids('tvmiddleware_video_genres', 'video_id', video_id_map, video_genres)
# replace_many_ids('tvmiddleware_video_genres', 'genre_id', genre_id_map, video_genres)
video_genres_id_map = insert('tvmiddleware_video_genres', video_genres)

video_stream_services = to_list(get_by_list('tvmiddleware_video_stream_services', 'video_id', video, 0))
# replace_many_ids('tvmiddleware_video_stream_services', 'video_id', video_id_map, video_stream_services)
# replace_many_ids('tvmiddleware_video_stream_services', 'streamservice_id', streamservice_id_map, video_stream_services)
video_stream_services_id_map = insert('tvmiddleware_video_stream_services', video_stream_services)

video_tariffs = to_list(get_by_list('tvmiddleware_video_tariffs', 'video_id', video, 0))
# replace_many_ids('tvmiddleware_video_tariffs', 'video_id', video_id_map, video_tariffs)
# replace_many_ids('tvmiddleware_video_tariffs', 'tariff_id', tariff_id_map, video_tariffs)
video_tariffs_id_map = insert('tvmiddleware_video_tariffs', video_tariffs)

videofile = to_list(get_by_list('tvmiddleware_videofile', 'video_id', video, 0))
# replace_many_ids('tvmiddleware_videofile', 'video_id', video_id_map, videofile)
videofile_id_map = insert('tvmiddleware_videofile', videofile)

message = to_list(get_by_list('tvmiddleware_message', 'customer_id', customer, 0))
# replace_many_ids('tvmiddleware_message', 'customer_id', customer_id_map, message)
message_id_map = insert('tvmiddleware_message', message)

print "Copy accounts"

account = to_list(get_by('tvmiddleware_account', 'client_id', client_id))
replace_id('tvmiddleware_account', 'client_id', new_client_id, account)
# replace_many_ids('tvmiddleware_account', 'customer_id', customer_id_map, account)
# replace_many_ids('tvmiddleware_account', 'data_center_id', datacenter_id_map, account)
# replace_many_ids('tvmiddleware_account', 'device_id', play_id_map, account)
# replace_many_ids('tvmiddleware_account', 'template_id', template_id_map, account)
# replace_many_ids('tvmiddleware_account', 'city_id', city_id_map, account)
# replace_many_ids('tvmiddleware_account', 'country_id', country_id_map, account)
account_id_map = insert('tvmiddleware_account', account)

accountauthkey = to_list(get_by('tvmiddleware_accountauthkey', 'client_id', client_id))
replace_id('tvmiddleware_accountauthkey', 'client_id', new_client_id, accountauthkey)
# replace_many_ids('tvmiddleware_accountauthkey', 'account_id', account_id_map, accountauthkey)
accountauthkey_id_map = insert('tvmiddleware_accountauthkey', accountauthkey)

accountchannel = to_list(get_by_list('tvmiddleware_accountchannel', 'account_id', account, 0))
# replace_many_ids('tvmiddleware_accountchannel', 'account_id', account_id_map, accountchannel)
# replace_many_ids('tvmiddleware_accountchannel', 'channel_id', channel_id_map, accountchannel)
accountchannel_id_map = insert('tvmiddleware_accountchannel', accountchannel)

accountdevice = to_list(get_by('tvmiddleware_accountdevice', 'client_id', client_id))
replace_id('tvmiddleware_accountdevice', 'client_id', new_client_id, accountdevice)
# replace_many_ids('tvmiddleware_accountdevice', 'account_id', account_id_map, accountdevice)
# replace_many_ids('tvmiddleware_accountdevice', 'device_id', play_id_map, accountdevice)
accountdevice_id_map = insert('tvmiddleware_accountdevice', accountdevice)

accountgamerecord = to_list(get_by_list('tvmiddleware_accountgamerecord', 'account_id', account, 0))
# replace_many_ids('tvmiddleware_accountgamerecord', 'account_id', account_id_map, accountgamerecord)
# replace_many_ids('tvmiddleware_accountgamerecord', 'game_id', game_id_map, accountgamerecord)
accountgamerecord_id_map = insert('tvmiddleware_accountgamerecord', accountgamerecord)

npvrtasks = to_list(get_by_list('tvmiddleware_npvrtasks', 'account_id', account, 0))
# replace_many_ids('tvmiddleware_npvrtasks', 'account_id', account_id_map, npvrtasks)
# replace_many_ids('tvmiddleware_npvrtasks', 'epg_id', epg_id_map, npvrtasks)
# replace_many_ids('tvmiddleware_npvrtasks', 'stream_service_id', streamservice_id_map, npvrtasks)
npvrtasks_id_map = insert('tvmiddleware_npvrtasks', npvrtasks)

maintenance = to_list(get_by('tvmiddleware_maintenance', 'client_id', client_id))
replace_id('tvmiddleware_maintenance', 'client_id', new_client_id, maintenance)
maintenance_id_map = insert('tvmiddleware_maintenance', maintenance)

maintenance_channels = to_list(get_by_list('tvmiddleware_maintenance_channels', 'maintenance_id', maintenance, 0))
# replace_many_ids('tvmiddleware_maintenance_channels', 'maintenance_id', maintenance_id_map, maintenance_channels)
# replace_many_ids('tvmiddleware_maintenance_channels', 'channel_id', channel_id_map, maintenance_channels)
maintenance_channels_id_map = insert('tvmiddleware_maintenance_channels', maintenance_channels)

maintenance_stream_services = to_list(get_by_list('tvmiddleware_maintenance_stream_services', 'maintenance_id', maintenance, 0))
# replace_many_ids('tvmiddleware_maintenance_stream_services', 'maintenance_id', maintenance_id_map, maintenance_stream_services)
# replace_many_ids('tvmiddleware_maintenance_stream_services', 'streamservice_id', streamservice_id_map, maintenance_stream_services)
maintenance_stream_services_id_map = insert('tvmiddleware_maintenance_stream_services', maintenance_stream_services)
"""
# widget
print "Copy widget"

widget = to_list(get_by('widgets_widget', 'client_id', client_id))
replace_id('widgets_widget', 'client_id', new_client_id, widget)
widget_id_map = insert('widgets_widget', widget)

widgetproperty = to_list(get_by_list('widgets_widgetproperty', 'widget_id', widget, 0))
# replace_many_ids('widgets_widgetproperty', 'widget_id', widget_id_map, widgetproperty)
widgetproperty_id_map = insert('widgets_widgetproperty', widgetproperty)

widgettoken = to_list(get_by_list('widgets_widgettoken', 'widget_id', widget, 0))
# replace_many_ids('widgets_widgettoken', 'widget_id', widget_id_map, widgettoken)
widgettoken_id_map = insert('widgets_widgettoken', widgettoken)
"""
# BILLING
print "Copy billing"

contract = to_list(get_by_list('billing_contract', 'customer_id', customer, 0))
# replace_many_ids('billing_contract', 'customer_id', customer_id_map, contract)
contract_id_map = insert('billing_contract', contract)

customerbankaccount = to_list(get_by_list('billing_customerbankaccount', 'customer_id', customer, 0))
# replace_many_ids('billing_customerbankaccount', 'customer_id', customer_id_map, customerbankaccount)
customerbankaccount_id_map = insert('billing_customerbankaccount', customerbankaccount)

customertransaction = to_list(get_by_list('billing_customertransaction', 'customer_id', customer, 0))
# replace_many_ids('billing_customertransaction', 'customer_id', customer_id_map, customertransaction)
customertransaction_id_map = insert('billing_customertransaction', customertransaction)

documenttemplate = to_list(get_by('billing_documenttemplate', 'client_id', client_id))
replace_id('billing_documenttemplate', 'client_id', new_client_id, documenttemplate)
documenttemplate_id_map = insert('billing_documenttemplate', documenttemplate)

invoice = to_list(get_by_list('billing_invoice', 'contract_id', contract, 0))
# replace_many_ids('billing_invoice', 'contract_id', contract_id_map, invoice)
invoice_id_map = insert('billing_invoice', invoice)

document = to_list(get_by_list('billing_document', 'contract_id', contract, 0))
# replace_many_ids('billing_document', 'contract_id', contract_id_map, document)
# replace_many_ids('billing_document', 'customer_id', customer_id_map, document)
# replace_many_ids('billing_document', 'document_template_id', documenttemplate_id_map, document)
# replace_many_ids('billing_document', 'invoice_id', invoice_id_map, document)
document_id_map = insert('billing_document', document)

invoiceitem = to_list(get_by_list('billing_invoiceitem', 'invoice_id', invoice, 0))
# replace_many_ids('billing_invoiceitem', 'invoice_id', invoice_id_map, invoiceitem)
invoiceitem_id_map = insert('billing_invoiceitem', invoiceitem)

paypalmerchantdata = to_list(get_by('billing_paypalmerchantdata', 'client_id', client_id))
replace_id('billing_paypalmerchantdata', 'client_id', new_client_id, paypalmerchantdata)
paypalmerchantdata_id_map = insert('billing_paypalmerchantdata', paypalmerchantdata)

product = to_list(get_by('billing_product', 'client_id', client_id))
replace_id('billing_product', 'client_id', new_client_id, product)
product_id_map = insert('billing_product', product)

w1cardmerchantdata = to_list(get_by('billing_w1cardmerchantdata', 'client_id', client_id))
replace_id('billing_w1cardmerchantdata', 'client_id', new_client_id, w1cardmerchantdata)
w1cardmerchantdata_id_map = insert('billing_w1cardmerchantdata', w1cardmerchantdata)

w1merchantdata = to_list(get_by('billing_w1merchantdata', 'client_id', client_id))
replace_id('billing_w1merchantdata', 'client_id', new_client_id, w1merchantdata)
w1merchantdata_id_map = insert('billing_w1merchantdata', w1merchantdata)

# Users

print "Copy users"

user = to_list(get_by('auth_user', 'client_id', client_id))
replace_id('auth_user', 'client_id', new_client_id, user)
# replace_many_ids('auth_user', 'dealer_id', dealer_id_map, user)
user_id_map = insert('auth_user', user)

user_groups = to_list(get_by_list('auth_user_groups', 'user_id', user, 0))
# replace_many_ids('auth_user_groups', 'user_id', user_id_map, user_groups)

group = to_list(get_by_list('auth_group', 'id', user_groups, 3))
group_id_map = insert('auth_group', group)

# replace_many_ids('auth_user_groups', 'group_id', group_id_map, user_groups)
user_groups_id_map = insert('auth_user_groups', user_groups)

# permission = get_all('auth_permission')
# # replace_many_ids('auth_permission', 'content_type_id', content_type_id_map, permission)
# permission_id_map = insert('auth_permission', permission)

group_permissions = to_list(get_by_list('auth_group_permissions', 'group_id', group, 0))
# replace_many_ids('auth_group_permissions', 'group_id', group_id_map, group_permissions)
# # replace_many_ids('auth_group_permissions', 'permission_id', permission_id_map, group_permissions)
group_permissions_id_map = insert('auth_group_permissions', group_permissions)

user_user_permissions = to_list(get_by_list('auth_user_user_permissions', 'user_id', user, 0))
# replace_many_ids('auth_user_user_permissions', 'user_id', user_id_map, user_user_permissions)
# # replace_many_ids('auth_user_user_permissions', 'permission_id', permission_id_map, user_user_permissions)
user_user_permissions_id_map = insert('auth_user_user_permissions', user_user_permissions)

## ATTENTION! Code above was generated.

print "OK"
