# -*- coding: utf-8 -*-


def get_tariff(tariff, tariff_map):
    """
    Получает ID тарифа из Smarty по ID тарифа из биллинга
    """
    try:
        tariff_id = int(tariff)
    except:
        return None
    for key in tariff_map:
        if tariff_id in tariff_map[key]:
            return key
    return None


def get_tariff_list(raw_tariff_list, tariff_map):
    """
    Получает список ID тарифов из Smarty по списку ID тарифов из биллинга.
    Тарифы не дублируются, если соответствие не найдено - тариф игнорируется
    """
    tariff_list = []
    for raw_tariff in raw_tariff_list:
        tariff = get_tariff(raw_tariff, tariff_map)
        if tariff is not None and tariff not in tariff_list:
            tariff_list.append(tariff)
    return tariff_list


def get_any_billing_tariff(tariff, tariff_map):
    """
    Возвращает первый ID тарифа из биллинга по ID тарифа из Smarty
    Возвращает первый ID из списка, если их несколько
    Если соответствие не найдено, то возвращает -1
    """
    try:
        tariff_id = int(tariff)
    except:
        return -1

    tariff_list = tariff_map.get(tariff_id, None)
    if not tariff_list:
        return -1
    return tariff_list[0]


def get_all_billing_tariffs(tariff, tariff_map):
    """
    Возвращает список соответствий ID тарифа из биллинга тарифу из Smarty
    """
    try:
        tariff_id = int(tariff)
    except:
        return []

    return tariff_map.get(tariff_id, [])


def get_inverted_tariff_list(tariff_list, tariff_map):
    """
    Получает список ID тарифов из Smarty, для которых не найдено соответствующих
    тарифов в списке ID тарифов из биллинга, тарифы не дублируются
    """
    out_list = []
    for tariff in tariff_map.keys():
        if tariff not in tariff_list:
            out_list.append(tariff)
    return out_list
