# DocAssist AI

Демонстрационный помощник по синтетическим регламентам. Запуск:

```bash
cp .env.example .env
docker compose up --build -d
```

Откройте http://localhost:8501. Для вопросов с генерацией ответа нужен `GIGACHAT_AUTH_KEY` в `.env`. Значение — ключ авторизации Base64 из кабинета GigaChat, не access token. `GIGACHAT_SCOPE` принимает `GIGACHAT_API_PERS`, `GIGACHAT_API_B2B` или `GIGACHAT_API_CORP`. `GIGACHAT_MODEL` задаёт доступную для аккаунта модель. При отсутствии ключа интерфейс сообщает об этом и сохраняет доступ к документам, версиям и шаблонам.

Образ устанавливает корневой сертификат НУЦ Минцифры для TLS-соединения с GigaChat согласно [официальной инструкции](https://developers.sber.ru/docs/ru/gigachat/certificates). Проверка TLS не отключается для API-запросов.

Чтобы включить операции администратора, создайте пароль и запишите его PBKDF2-хеш в `DOCASSIST_ADMIN_PASSWORD_HASH`. Генератор: `docker compose run --rm app python scripts/hash_password.py`. Полученную строку добавьте в `.env`, затем перезапустите контейнер. Без хеша административный вход закрыт.

Тесты: `docker compose run --rm app pytest -q`. Данные и исходники находятся в `data/`; каталог монтируется в контейнер и переживает перезапуск. Приложение не меняет старую таблицу `chunks` прототипа, новые таблицы создаются рядом. Загруженные редакции хранятся в `data/uploads/`.

Ограничения и результаты проверки перечислены в [отчёте](docs/demo/TEST_REPORT.md).
