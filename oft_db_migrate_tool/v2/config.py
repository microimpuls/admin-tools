OFT_DB_HOST = ""
OFT_DB_NAME = ""
OFT_DB_USER = ""
OFT_DB_PASS = ""

SMARTY_DB_HOST = ""
SMARTY_DB_NAME = ""
SMARTY_DB_USER = ""
SMARTY_DB_PASS = ""

EML_PATH = "eml"

DOMAIN = "example.com"

COUNTRY_ID = 7716094

CLIENT_ID = 1

CURRENCY_ID = 2 # USD

DEFAULT_PAYMENT_TYPE = 2 # Paypal

QUERY_CUSTOM_ENDING = ""

# Key = OFT stb_id
# Value = new device_id from tvmiddleware_playdevice
DEVICE_ID_MAP = {
    '17': None, # SIG
    '18': None, # MAXIBOX
    '19': None, # TELSEY
    '20': None, # AirTies
    '23': 3, # MAG
    '24': 19, # Dune
    '25': None, # OFT PC-Client
    '26': 1, # Samsung Smart TV
    '27': None # Enigma
}

# Hint:
# select t.id, tbl.name from g_Tariffs t left join g_Tariff_BrandsLng tbl on (tbl.tariff_brand_id = t.tarif_brand_id)

TARIFF_ID_MAP = {
    '1': (1, 5, 6),
    '3': (4,),
    '5': (4,),
    '8': (7,),
    '11': (8,),
    '12': (9,),
    '13': (1, 5, 6),
    '14': (1, 5, 6),
    '15': (2,),
    '16': (3,),
    '18': (1, 5),
    '21': (1, 6),
    '25': (1,),
}

DATACENTER_ID_MAP = {
    '1': None, # auto
    '2': None, # test
    '3': None, # LA Israel
    '5': None, # Europe
    '7': None, # FC
    '8': None, # FR
    '9': None, # NN
    '10': 3, # Rishon, Interhost
    '12': 4 # SoftLayer
}
