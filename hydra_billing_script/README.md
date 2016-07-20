Скрипты интеграции биллинга Hydra с Microimpuls Middleware (Smarty)
===================================================================

Интеграция осуществляется со стороны Hydra через вызов скрипта по событиям биллинга.
Вызываемый скрипт ``smarty_billing_api_wrapper.py``, а также библиотека ``smarty_billing_client.py``
должен быть размещены на сервере биллинга и доступны для запуска из событийного интерпретатора биллинга.

Скрипт позволяет создавать и активировать аккаунты, подключать и отключать тарифные планы из биллинговой системы.
Деактивация аккаунта производится путем отключения тарифных планов.

В скрипте ``smarty_billing_api_wrapper.py`` необходимо настроить параметры доступа к Smarty Billing API
(см. [Документация по Billing API](http://mi-smarty-docs.readthedocs.io/ru/latest/integration.html#billing-api)
и [Настройка клиента](http://mi-smarty-docs.readthedocs.io/ru/latest/service_configuration.html#client-creation)):

*HOST*: URL-адрес Billing API
*CLIENT_ID*: Идентификатор оператора.
*API_KEY*: Ключ для Billing API.

А также таблицу ассоциации тарифных пакетов в Hydra к тарифным планам в Smarty, пример:
```
tariffs = {
    2: (1, 2, 3, 4),
    3: (5, 6, 7, 8),
}
```

Примечание: ключ массива - ID тарифного плана в Smarty, а значение - список ID тарифных пакетов в Hydra.

Документация по Hydra: http://wiki.latera.ru/pages/viewpage.action?pageId=33947732

Пример настройки событий в Hydra
--------------------------------

Событие на оборудовании абонента при включении/отключении услуги доступа:

``/opt/hydra/scripts/smarty_billing_api_wrapper.py add_user_tariff  $USER_ID $USER_ACCOUNT $SUBSC_SERVS_LIST``

``/opt/hydra/scripts/smarty_billing_api_wrapper.py remove_user_tariff $USER_ID $USER_ACCOUNT $SUBSC_SERVS_LIST``

Дополнительная интеграция со стороны абонентского приложения
------------------------------------------------------------

Скрипты ``hydra_adapter.py`` и ``hydra_adapter_server.py`` позволяют осуществить интеграцию со стороны Smarty для таких функций, как:
* Привязка/отвязка MAC-адреса приставки к ЛС абонента в Hydra
* Запрос баланса
* Запрос списка подключенных услуг и их стоимостей
* Проведение обещанного платежа

``hydra_adapter_server.py`` представляет собой веб-приложение на базе фреймфорвка Flask и может быть запущен на сервере
абонентского портала Middleware через uwsgi, пример конфига hydra-billing-backend.ini:
```
[uwsgi]
master = true
workers = 16
socket = /tmp/hydra-billing-backend.uwsgi.sock
pythonpath = /etc/microimpuls/smarty/custom
module = hydra_adapter_server:app
chmod-socket = 664
vacuum = true
plugins = python
```

Для подключения этих функций абонентский портал кастомизируется внешним приложением "Баланс", а также на уровне событий портала.

Скриншоты внешнего приложения "Баланс" шаблона ``focus``:

![Главное меню](/preview/focus_balance_menu.jpg)

Пример скрипта кастомизации для привязки приставки:
```
var CLIENT_SETTINGS = {
...
};

OnAccountLoginSuccessful = function()
{
    var abonement = App.settings.getAbonement();
    var mac = App.device.getMacAddress();
    var serial = App.device.getSerialNumber();
    var XHRObj = new XMLHttpRequest();
    if (XHRObj) {
        XHRObj.open("GET", "/hydra/add_device?account_id=" + abonement + "&mac=" + mac + "&serial=" + serial, true);
        XHRObj.send();
    }
};
```
