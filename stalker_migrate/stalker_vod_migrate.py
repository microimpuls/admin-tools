#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Stalker VOD Migrate script

Формат запуска:
$ python stalker_vod_migrate.py <input_csv_filename.csv> <method_name> <params>

Доступные методы:

resolve_filenames - функция определяет имена файлов на vod-сервере stalker по полю video.path и обновляет этими данными CSV выгрузку.
Требуется запускать в случае, если в БД нет информации об именах файлов, а только пути.
Запускать на сервере vod, в качестве аргумента - путь к директории, в которой хранятся файлы, например /media/RAID5/storage.

resolve_posters - функция определяет путь до постера фильма согласно алгоритму сохранения скриншотов в Stalker (обычно директория /stalker_portal/screenshots).
В качестве аргумента принимает URL path до директории с постерами в Smarty.
Входящий файл модифицируется этими данными.

prepare_sql - функция готовит SQL команды для импорта VOD в Smarty DB. 
В качестве аргумента принимает client_id.

Пример вызова скрипта см. ниже.

Скрипт работает с CSV выгрузкой VOD-фильмов в формате:
name,name_orig,kinopoisk_id,description,year,actors,countries,director,created_at,genre1,genre2,genre3,path,poster,duration

SQL скрипт получения такой выгрузки для БД stalker:
SELECT
    v.name, v.o_name AS 'name_orig', v.kinopoisk_id, REPLACE(REPLACE(v.description, '\"', '"'), '"', "'") AS 'description',
    v.year, v.actors, v.country AS 'countries', v.director, v.added AS 'created_at',
    cg1.title AS 'genre1', cg2.title AS 'genre2', cg3.title AS 'genre3',
    path, ss.id as 'poster', v.time AS 'duration'
FROM video v
LEFT JOIN cat_genre cg1 ON (cg1.id = v.cat_genre_id_1)
LEFT JOIN cat_genre cg2 ON (cg2.id = v.cat_genre_id_2)
LEFT JOIN cat_genre cg3 ON (cg3.id = v.cat_genre_id_3)
LEFT JOIN screenshots ss ON (ss.media_id = v.id)
ORDER BY created_at ASC

Перед запуском рекомендуется очистить видеотеку Smarty:
DELETE FROM tvmiddleware_video_genres;
DELETE FROM tvmiddleware_videofile;
DELETE FROM tvmiddleware_video;
DELETE FROM tvmiddleware_genre;

На выходе после выполнения всех функций скрипт подготавливает SQL-скрипт для импорта в Smarty БД.

Пример запуска:
stalker@storage:~/mi$ python stalker_vod_migrate.py query_result.csv resolve_filenames /media/RAID5/storage/
stalker@storage:~/mi$ python stalker_vod_migrate.py query_result.csv resolve_posters http://smarty.example.com:8180/media/upload/stalker
stalker@storage:~/mi$ python stalker_vod_migrate.py query_result.csv prepare_sql 1

(c) ksotik, Microimpuls LLC 2016
"""

import sys, csv, os

def resolve_filenames(file_name, storage_path):
    output = []
    with open(file_name, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for s in reader:
            if len(s) < 14: continue
            if s[0] == 'name': continue
            path = '%s/%s' % (storage_path, s[12])
            try:
                files = os.listdir(path)
            except:
                files = []
            movie_file_name = ''
            for f in files:
                e = f.split('.')
                if e[-1] == 'md5':
                    continue
                movie_file_name = f
            s[12] = '%s/%s' % (s[12], movie_file_name)
            output.append(s)
    if len(output) > 0:
        with open(file_name, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for s in output:
                writer.writerow(s)


def resolve_posters(file_name, screenshots_path):
    output = []
    with open(file_name, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for s in reader:
            if len(s) < 14: continue
            if s[0] == 'name': continue
            screenshot_id = s[13]
            try:
                a = int(screenshot_id)/100 + 1
                s[13] = '%s/%d/%s.jpg' % (screenshots_path, a, screenshot_id)
            except:
                continue
            output.append(s)
    if len(output) > 0:
        with open(file_name, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for s in output:
                writer.writerow(s)


def prepare_sql(file_name, client_id):
    queries = []
    genres = []
    def insert_genre(genre):
        if genre and genre != "NULL" and genre not in genres:
            genres.append(genre)
            q = "INSERT IGNORE INTO tvmiddleware_genre (name, sort, client_id) VALUES('%s', '%d', '%s');" % (genre, 0, client_id)
            queries.append(q)

    def insert_video_genre(video_id, genre):
        if genre and genre != "NULL":
            q = "INSERT IGNORE INTO tvmiddleware_video_genres (video_id, genre_id) VALUES(" \
                "%s, (SELECT id FROM tvmiddleware_genre WHERE name = '%s' AND client_id = '%s' LIMIT 1));" % (video_id, genre, client_id)
            queries.append(q)

    def clean_arr(s):
        for i in range(0, len(s)):
            try:
                s[i] = s[i].strip()
                s[i] = s[i].replace("'", "\\'")
            except:
                s[i] = ""

    insert_genre("other")

    with open(file_name, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for s in reader:
            if len(s) < 15: continue
            if s[0] == 'name': continue
            # name,name_orig,kinopoisk_id,description,year,actors,countries,director,created_at,genre1,genre2,genre3,path,poster,duration

            clean_arr(s)

            insert_genre(s[9])
            insert_genre(s[10])
            insert_genre(s[11])

            q = "INSERT INTO tvmiddleware_video (name, kinopoisk_id, name_orig, description, year, poster_url, actors, countries, director, client_id, created_at) " \
                "VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % (s[0], s[2], s[1], s[3], s[4], s[13], s[5], s[6], s[7], client_id, s[8])
            queries.append(q)

            q = "SET @last_id = LAST_INSERT_ID();"
            queries.append(q)

            insert_video_genre("@last_id", s[9])
            insert_video_genre("@last_id", s[10])
            insert_video_genre("@last_id", s[11])

            if (not s[9] or s[9] == "NULL") and (not s[10] or s[10] == "NULL") and (not s[11] or s[11] == "NULL"):
                insert_video_genre("@last_id", "other")

            q = "INSERT INTO tvmiddleware_videofile (name, filename, duration, video_id) " \
                "VALUES('%s', '%s', '%s', @last_id);" % (s[0], s[12], s[14])
            queries.append(q)
    with open('%s_output.sql' % file_name, 'w') as output:
        for q in queries:
            output.write(q + '\n')

func = {
    'resolve_filenames': resolve_filenames,
    'resolve_posters': resolve_posters,
    'prepare_sql': prepare_sql,
}

def handler():
    if len(sys.argv) < 4:
        print '$ python stalker_vod_migrate.py <input_csv_filename.csv> <method_name> <params>'
        return

    file_name = sys.argv[1]
    func_name = sys.argv[2]
    args = sys.argv[3]
    if func_name not in func:
        return
    try:
        func[func_name](file_name, args)
    except Exception as e:
        print e.message

handler()
