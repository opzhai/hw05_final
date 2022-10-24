# Социальная сеть YaTube

Социальная сеть блогеров - сеть с возможностью создания, просмотра, редактирования и удаления записей. Реализован механизм подписки на понравившихся авторов и отслеживание их записей. Покрытие тестами. Возможность добавления изображений.

## Инструментарий:
  * Django 2.2
  * Python 3.7
  * Django Unittest
  * Django debug toolbar
  * PostgreSQL
  * Django ORM

## Установка:
  * клонируйте репозиторий к себе на компьютер

## Запуск:
  * Установка зависимостей:
    * `pip install -r requirements.txt`
  * Применение миграций:
    * `python manage.py makemigrations`
    * `python manage.py migrate`
  * Создание администратора:
    * `python manage.py createsuperuser`
  * Запуск приложения:
    * `python manage.py runserver`
***
### Автор
Александр Позжаев
