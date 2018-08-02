# -*- coding:utf-8 -*-

# Список видеофайлов, формат:
# video_path: (file_names, streamservice_id)
# Список можно сгенерировать, запустив функцию данный скрипт и подав на
# страндартный вход список файлов в формате "./Path/File.ts" (файлы раздляются переводом строки)
# Список всех файлов в директории рекурсивно можно получить с помощью вызова find
# Путь у конкретного фильма должен совпадать с полем path таблицы video в БД Stalker


import fileinput


videos = {
    u'Path': ([u'File.ts'], 3),
}


SERVER_ID = 3


def is_file_is_uselss(file):
    """
    Ignore this file extensions
    """
    return file[file.rfind('.') + 1:] in ['md5']


def is_file_not_video(file):
    """
    Ignore this file extensions
    """
    return file[file.rfind('.') + 1:] in ['srt', 'ac3', 'smi']


def parse_file(str, server_id):

    str = str.decode('utf8')
    path = str[2:str.find('/', 2)]
    if len(path) == 0:
        return

    file = str[str.find('/', 2) + 1:].strip()
    if is_file_is_uselss(file) or is_file_not_video(file):
        return

    if path in videos:
        videos[path][0].append(file)
    else:
        videos[path] = ([file], server_id)


def run():
    """
    Parse stdin
    """
    for line in fileinput.input():
        parse_file(line, SERVER_ID)
    print unicode(videos).replace(u'),', u'),\n')


if __name__ == "__main__":
    run()
