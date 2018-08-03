# -*- coding:utf-8 -*-


# Список жанров, формат: smarty_genre_id: [stalker_genre_ids]
# Список жанров в Stalker: select * from cat_genre;

genres = {
    1: [1, 2, 3],
    3: [4, 5],
}

# Список категорий, формат stalker_category_id: smarty_genre_id (формат, обратный предыдущему)
# Список категорий в Stalker: select * from media_category;

categories = {
    1: 3,
    2: 2,
}


def convert_genre(stalker_genre):
    if stalker_genre == 0:
        return 0

    for genre in genres:
        if stalker_genre in genres[genre]:
            return genre
    return 0


def convert_category(stalker_genre):
    if stalker_genre == 0:
        return 0
    return categories.get(stalker_genre, 0)