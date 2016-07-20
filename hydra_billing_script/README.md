Скрипты интеграции биллинга Гидра с Microimpuls Middleware (Smarty)
===================================================================

Биллинг "Гидра": http://www.hydra-billing.ru

Интеграция осуществляется со стороны Гидры через вызов скрипта по событиям биллинга.
Вызываемый скрипт ``smarty_billing_api_wrapper.py``, а также библиотека ``smarty_billing_client.py``
должен быть размещены на сервере биллинга и доступны для запуска из событийного интерпретатора биллинга.

Скрипт позволяет создавать и активировать аккаунты, подключать и отключать тарифные планы из биллинговой системы.
Деактивация аккаунта производится путем отключения тарифных планов.

В скрипте ``smarty_billing_api_wrapper.py`` необходимо настроить параметры доступа к Smarty Billing API
(см. [Документация по Billing API](http://mi-smarty-docs.readthedocs.io/ru/latest/integration.html#billing-api)
и [Настройка клиента](http://mi-smarty-docs.readthedocs.io/ru/latest/service_configuration.html#client-creation)):

**HOST**: URL-адрес Billing API

**CLIENT_ID**: Идентификатор оператора.

**API_KEY**: Ключ для Billing API.

А также таблицу ассоциации тарифных пакетов в Гидре к тарифным планам в Smarty, пример:
```
tariffs = {
    2: (1, 2, 3, 4),
    3: (5, 6, 7, 8),
}
```

Примечание: ключ массива - ID тарифного плана в Smarty, а значение - список ID тарифных пакетов в Гидре.

Документация по Hydra: http://wiki.latera.ru/pages/viewpage.action?pageId=33947732

Пример настройки событий в Гидре
--------------------------------

Событие на оборудовании абонента при включении/отключении услуги доступа:

``/opt/hydra/scripts/smarty_billing_api_wrapper.py add_user_tariff  $USER_ID $USER_ACCOUNT $SUBSC_SERVS_LIST``

``/opt/hydra/scripts/smarty_billing_api_wrapper.py remove_user_tariff $USER_ID $USER_ACCOUNT $SUBSC_SERVS_LIST``

Дополнительная интеграция со стороны абонентского приложения
------------------------------------------------------------

Скрипты ``hydra_adapter.py`` и ``hydra_adapter_server.py`` позволяют осуществить интеграцию со стороны Smarty напрямую в Hydra через вызов хранимых процедур в Oracle для таких функций, как:
* Привязка/отвязка MAC-адреса приставки к ЛС абонента в Hydra
* Запрос баланса
* Запрос списка подключенных услуг и их стоимостей
* Проведение обещанного платежа

``hydra_adapter_server.py`` представляет собой веб-приложение на базе фреймфорвка Flask и может быть запущено на сервере
Smarty через uwsgi + nginx, пример конфигурации uwsgi hydra-billing-backend.ini:
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

Пример конфигурации nginx:
```
upstream mw1-hydra-billing-backend {
    server unix:/tmp/hydra-billing-backend.uwsgi.sock;
}

server {
    listen 127.0.0.1:65080;

    access_log /var/log/nginx/microimpuls/hydra-billing-backend/nginx.access_log;
    error_log /var/log/nginx/microimpuls/hydra-billing-backend/nginx.error_log;

    charset utf-8;

    location / {
        uwsgi_pass mw1-hydra-billing-backend;
        include uwsgi_params;
    }
}

```

Для подключения этих функций абонентский портал кастомизируется внешним приложением "Баланс", а также на уровне событий портала.

Скриншоты внешнего приложения "Баланс" шаблона ``focus``:

![Главное меню](/hydra_billing_script/preview/focus_balance_menu.jpg)
![Выбор лицевого счета](/hydra_billing_script/preview/focus_balance_account.jpg)
![Список подключенных услуг и баланс](/hydra_billing_script/preview/focus_balance_services.jpg)
![Информация об обещанном платеже](/hydra_billing_script/preview/focus_balance_promised_payment.jpg)
![Статус проведения обещанного платежа](/hydra_billing_script/preview/focus_balance_promised_payment_info.jpg)

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
