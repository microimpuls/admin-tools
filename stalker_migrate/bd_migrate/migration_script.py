# -*- coding:utf-8 -*-
from __future__ import print_function

import re
import traceback
import datetime
import io
from dateutil import parser
from warnings import filterwarnings

import MySQLdb
import genre_mapping
import video_list


"""
REQUEST_LIMIT - максимальное количество фильмов мигрируемое за раз
CLIENT_ID - ID клиента
IMAGE_PREFIX - путь до постера, который будет записан в БД (общий путь будет записан как IMAGE_PREFIX + имя файла)
DEBUG - включает дублировыние лога в stdout, выполняет не больше одного цикла
LOG_FILE - файл лога
STATE_FILE - файл, в котором хранится состояние (количество мигрировынных фильмов)
TARIFFS - список ID тарифов, подключаемых по умолчанию
STREAMING_SERVICES - список ID сервисов, подключаемых по умолчанию
MAX_ACTORS - максимальное количество актёров, записываемое в поле actors

Наличие непустого STATE_FILE обязательно

Перед выполенением миграции нужно заполнить отображения жанров, категорий (genre_mapping.py) и фильмов (video_list.py).
Жанры в Smarty нужно создать заранее.

Парсинг списка актёров: parse_actors.
Настройка ассетов, в том числе генерация для них имён файлов и названий: get_assets_for_video.
Генерации имени файла для постера: make_image_url.

Актёры добавляются в БД Smarty автоматически.
"""

REQUEST_LIMIT = 5
CLIENT_ID = 1
IMAGE_PREFIX = 'upload/tvmiddleware/posters/'
DEBUG = True
LOG_FILE = 'migrate.log'
STATE_FILE = 'last_movie.state'

MAX_ACTORS = 3

TARIFFS = [1]

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWD = 'rootpsswd'
DB_NAME = 'smarty'

STALKER_DB_HOST = ''
STALKER_DB_USER = 'iptv'
STALKER_DB_PASSWD = ''
STALKER_DB_NAME = 'stalker_db'

ACTOR_DICT = {}

# Инициализация соедниения
smarty_conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWD, db=DB_NAME, charset="utf8")
stalker_conn = MySQLdb.connect(host=STALKER_DB_HOST, user=STALKER_DB_USER,
                               passwd=STALKER_DB_PASSWD, db=STALKER_DB_NAME, charset="utf8")
filterwarnings('ignore', category=MySQLdb.Warning)

if LOG_FILE:
    logfile = io.open(LOG_FILE, 'a', encoding='utf8')
else:
    logfile = None


class Asset:
    file_name = ""
    is_trailer = False
    promo = ""
    name = ""  # есть только id
    length = 0  # длительность пропущена
    sort = 0


class Movie:
    id = 0  # ID из таблицы video
    name = ""
    alias = ""
    name_orig = ""
    year = None  # type - int
    date = None
    # released = None
    # added = ""
    # type = ""  # movie, series, track
    description = ""
    images = None
    assets = None
    genres = None
    actors = None
    actor_str = ''
    is_season = False
    # is_announcement = False
    countries = ""
    director = ""
    path = ""  # используется для генерации имён файлов
    uri = None  # Static URI

    # duration = 0??
    poster_big = ''
    poster_small = ''

    rating = 0
    kinopoisk_rating = 0
    imdb_rating = 0

    kinopoisk_id = 0
    stream_service = None
    # ext_id = None

    def __init__(self):
        self.images = []
        self.assets = []
        self.genres = []
        self.actors = []


# Сервисные функции:


def log(msg):
    if isinstance(msg, str):
        msg = msg.encode('utf8')
    full_msg = u"%s: %s\n" % (datetime.datetime.now().isoformat(), msg)
    if logfile:
        logfile.write(full_msg)
    if DEBUG:
        print(full_msg, end='')


def load_state():
    with io.open(STATE_FILE) as f:
        state = f.read()
        return int(state)


def write_state(state):
    with io.open(STATE_FILE, 'w') as f:
        f.write(unicode(state))


def parse_iso_date(iso_str):
    return parser.parse(iso_str)


# Функции для работы с БД:

def make_mysql_date(dt):
    if dt is None:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def make_mysql_bool(value):
    return 1 if value else 0


def load_lines(db, sql, args):
    cursor = db.cursor()
    cursor.execute(sql, args)
    return cursor.fetchall()


def load_id_in_dict(db, sql, args, obj_dict):
    objs = load_lines(db, sql, args)
    for pair in objs:
        obj_dict[pair[0]] = pair[1]


# ========================


def parse_actors(actor_str):
    """
    Разбирает строку с актёрами
    Здесь можно сделать набор костылей под разные варианты записи списка актёров
    """

    if not actor_str:
        return []

    actors = re.split('[\n,]', actor_str)
    actors = [actor.strip() for actor in actors if actor.strip()]
    return actors


def movie_from_line(line):
    movie = Movie()
    movie.name = line[0][:100]

    movie.name_orig = line[1]
    movie.description = line[2][:1000]  # Max description length -- 1000
    movie.date = line[3]
    movie.path = line[4]

    movie.genres = []
    for genre_id in [line[5], line[6], line[7], line[8]]:
        smarty_genre_id = genre_mapping.convert_genre(genre_id)
        if smarty_genre_id != 0:
            movie.genres.append(smarty_genre_id)

    movie.director = line[9][:100]   # Max director length -- 100
    movie.actors = parse_actors(line[10])
    movie.actor_str = ', '.join(movie.actors[:3])
    try:
        movie.year = int(line[11])
    except:
        movie.year = 0

    movie.date = line[12]
    movie.kinopoisk_id = line[13]
    if not movie.kinopoisk_id:
        movie.kinopoisk_id = 0

    movie.is_season = (line[14] == 1)
    movie.id = line[15]
    movie.kinopoisk_rating = line[16]
    if not movie.kinopoisk_rating:
        movie.kinopoisk_rating = 0
    movie.imdb_rating = line[17]
    try:
        movie.rating = int(line[18].replace("+", ""))
    except:
        movie.rating = 0

    category = genre_mapping.convert_category(line[20])
    if category != 0:
        movie.genres.append(category)

    movie.countries = line[21]
    return movie


def get_movies(offset, limit):
    fields = ["name", "o_name", "description", "time", "path", "cat_genre_id_1", "cat_genre_id_2",
              "cat_genre_id_3", "cat_genre_id_4", "director", "actors", "year", "added", "kinopoisk_id",
              "is_series", "id", "rating_kinopoisk", "rating_imdb", "age", "series", "category_id", "country"]
    sql = "select " + ",".join(fields) + " from video limit %d offset %d" % (limit, offset)
    lines = load_lines(stalker_conn, sql, {})

    if not (isinstance(lines, list) or isinstance(lines, tuple)):
        return []
    return [movie_from_line(line) for line in lines]


def make_image_url(poster_id):
    """
    Генерация имени постера по ID из таблицы screenshots
    """
    return IMAGE_PREFIX + str(poster_id) + ".jpg"


def get_assets_for_video(video):
    """
    Настройка асстов
    """
    entry = video_list.videos.get(video.path)
    if entry is None:
        # Пути в списке нет
        log("Dict entry is missed for video with path %s (id %d)" % (video.path, video.id))
        return [], None

    assets = []
    for asset_file in entry[0]:
        asset = Asset()

        short_name = asset_file[:asset_file.rfind('.')]

        # Генерация имени ассета
        if len(entry[0]) > 1:
            # Обычно файл серии имеет формат вроде <номер_серии>.mp4
            asset.name = u"Серия " + short_name
            asset.sort = short_name
        else:
            asset.name = u"Видео"
        asset.file_name = "%s/%s" % (video.path, asset_file)
        assets.append(asset)
    return assets


def get_ss_for_video(video):
    """
    Настройка стримсервисов для видео
    """
    entry = video_list.videos.get(video.path)
    if entry is None:
        return None
    return entry[1]


def get_poster_for_video(movie):
    """
    Настройка постеров для видео
    """
    posters = get_posters(movie.id)
    if len(posters) == 0:
        return ""
    return make_image_url(posters[0][0])


def load_next(offset, limit):
    """
    Загрузка следующей порции видео из БД Stalker
    """
    movies = get_movies(offset, limit)
    for movie in movies:
        movie.assets = get_assets_for_video(movie)
        movie.stream_service = get_ss_for_video(movie)

        if len(movie.assets) > 1:
            # Если ассетов больше одного - это сериал
            movie.is_season = True

        movie.poster_big = movie.poster_small = get_poster_for_video(movie)
    return movies


def get_actor_id(cursor, actor_name):
    if actor_name not in ACTOR_DICT:
        sql_template = """INSERT INTO tvmiddleware_actor (name,client_id,biography,profession,country,photo,gender,birthdate,
    biography_lang1,biography_lang2,biography_lang3,biography_lang4,biography_lang5,
    profession_lang1,profession_lang2,profession_lang3,profession_lang4,profession_lang5,
    country_lang1,country_lang2,country_lang3,country_lang4,country_lang5,
    birthdate_lang1,birthdate_lang2,birthdate_lang3,birthdate_lang4,birthdate_lang5,
    name_lang1,name_lang2,name_lang3,name_lang4,name_lang5)
    VALUES (%s,%s,'','','',NULL,NULL,NULL,'','','','','','','','','','','','','','','',NULL,NULL,NULL,NULL,NULL,'','','','','');"""
        cursor.execute(sql_template, (actor_name, CLIENT_ID))
        next_id = cursor.lastrowid
        ACTOR_DICT[actor_name] = next_id
    return ACTOR_DICT[actor_name]


def add_file_sql(cursor, asset, movie_id):
    sql_template = """
INSERT INTO tvmiddleware_videofile (name,filename,duration,video_id,is_trailer,ext_id,promo_image,
name_lang2,name_lang3,name_lang4,name_lang5,promo_image_lang1,promo_image_lang2,promo_image_lang3,
promo_image_lang4,promo_image_lang5,sort)
    VALUES (%s,%s,%s,%s,%s,'','','','','','','','','','','',%s);"""
    cursor.execute(sql_template, (asset.name, asset.file_name, 0, movie_id, make_mysql_bool(asset.is_trailer), asset.sort))


def write_movie(movie):
    log("write movie %s..." % movie.name)
    cursor = smarty_conn.cursor()

    def process_list(obj_list, func, *args):
        # Добавляем объекты, которые ещё не были добавлены
        id_list = []
        for obj in obj_list:
            obj_id = func(cursor, obj, *args)
            if obj_id and obj_id not in id_list:
                id_list.append(obj_id)
        return id_list

    def link_objects(id_list, sql):
        # Настраиваем связи между таблицами
        for obj_id in id_list:
            cursor.execute(sql, (next_id, obj_id))

    sql_template = """INSERT INTO tvmiddleware_video
(name,date,kinopoisk_id,name_orig,description,year,countries,director,created_at,is_season,kinopoisk_rating,
rating,poster_big,poster_small,duration,client_id,available_everywhere,parent_control,updated_at,external_api_config_id,
price_category_id,is_package,imdb_rating,published_from,published_to,
ext_id,average_customers_rating,copyright_holder_id,is_announcement,language,
language_lang1,language_lang2,language_lang3,language_lang4,language_lang5,
countries_lang1,countries_lang2,countries_lang3,countries_lang4,countries_lang5,
description_lang1,description_lang2,description_lang3,description_lang4,description_lang5,
director_lang1,director_lang2,director_lang3,director_lang4,director_lang5,
name_lang1,name_lang2,name_lang3,name_lang4,name_lang5,uri,actors,
poster_big_lang1,poster_big_lang2,poster_big_lang3,poster_big_lang4,poster_big_lang5,
poster_small_lang1,poster_small_lang2,poster_small_lang3,poster_small_lang4,poster_small_lang5)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,0,%s,NULL,NULL,0,0,NULL,NULL,NULL,0,NULL,0,NULL,
'','','','','','','','','','','','','','','','','','','','','','','','','',%s,%s,"","","","","","","","","","");"""

    actor_sql_template = """INSERT INTO tvmiddleware_video_actors_set (video_id,actor_id) VALUES (%s,%s);"""
    genre_sql_template = """INSERT INTO tvmiddleware_video_genres (video_id,genre_id) VALUES (%s,%s);"""
    tariff_sql_template = """INSERT INTO tvmiddleware_video_tariffs (video_id,tariff_id) VALUES (%s,%s);"""
    streamservice_sql_template = """INSERT INTO tvmiddleware_video_stream_services (video_id,streamservice_id) VALUES (%s,%s);"""

    cursor.execute(sql_template, (movie.name, make_mysql_date(movie.date), movie.kinopoisk_id, movie.name_orig,
                   movie.description, movie.year, movie.countries, movie.director, make_mysql_date(movie.date),
                   make_mysql_bool(movie.is_season), movie.kinopoisk_rating, movie.rating, movie.poster_big,
                   movie.poster_small, 0, CLIENT_ID, make_mysql_date(movie.date), movie.uri, movie.actor_str),)
    next_id = cursor.lastrowid
    log("movie id %s" % next_id)

    # Настраиваем связи между таблицами
    process_list(movie.assets, add_file_sql, next_id)

    actor_id_list = process_list(movie.actors, get_actor_id)
    link_objects(actor_id_list, actor_sql_template)

    link_objects(movie.genres, genre_sql_template)
    link_objects(TARIFFS, tariff_sql_template)
    if movie.stream_service is not None:
        link_objects([movie.stream_service], streamservice_sql_template)

    smarty_conn.commit()
    log("movie writen")


def get_posters(video_id):
    sql = "select id from screenshots where media_id = %s" % video_id
    return load_lines(stalker_conn, sql, {})


def main():
    log("\nSTART MIGRATION")
    log("load state...")
    try:
        current = load_state()
    except Exception as e:
        log("Can't load state, %s" % repr(e))
        raise e
    log("state loaded, offset %s" % current)

    log("load actors...")
    # загружем всех уже добавленных актёров
    load_id_in_dict(smarty_conn, "select name,id from tvmiddleware_actor where client_id=%s;", (CLIENT_ID,), ACTOR_DICT)
    log("loaded")

    while True:
        log("load objects, offset: %s, limit %s" % (current, REQUEST_LIMIT))
        objects = load_next(current, REQUEST_LIMIT)
        nobjects = len(objects)
        log("%s objects loaded" % nobjects)

        if nobjects == 0:
            break

        for obj in objects:
            write_movie(obj)
            current += 1
            write_state(current)

        if DEBUG:
            break


try:
    main()
except:
    log("something gone wrong, revert commit")
    log(traceback.format_exc())
    if not DEBUG:
        print(traceback.format_exc())
