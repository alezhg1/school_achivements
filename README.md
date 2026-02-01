## Аутентификация и пользователи
- Регистрация пользователей (register view)
- Вход/выход (login/logout)
- Профили пользователей (profile view)
- Кастомная модель пользователя CustomUser с полями role и teacher_status
- Роли: ученики, учителя, администраторы

## Управление достижениями
- Создание/редактирование достижений (Achievement модель)
- Связь достижений с учениками (ForeignKey student)
- Результаты достижений (result CharField)
- CRUD операции через Django Admin

## Классы и управление
- Модель Classroom
- Привязка учеников к классам
- Отчёты по классам (classroom_report.html)

## Админ-панель
- Кастомизация admin (admin.py)
- base_site.html - брендинг админки
- change_list.html - списки объектов

## Views (17+ функций)
```
accounts.views:
├── home() - главная страница
├── register() - регистрация
├── login_view() - авторизация
├── profile_view() - профиль
├── logout_view() - выход
├── classroom_report() - отчёт по классу
└── дополнительные views (полный список в views.py 17368 символов)
```

## Формы
```
accounts.forms:
├── формы регистрации
├── формы профиля  
├── формы достижений
├── формы классов (3439 символов кода)
```

## Templates (9+ страниц)
```
templates/accounts/:
├── base.html - базовый шаблон
├── home.html - главная
├── login.html - авторизация
├── profile.html - профиль
├── index.html - индекс
├── classroom_report.html - отчёт класса
└── admin templates
```

## Middleware
- Кастомный middleware (5237 строк)
- Обработка запросов/ответов
- Аутентификация/авторизация

## URLs
```
accounts.urls (2540 строк):
├── / - главная
├── /register/ - регистрация  
├── /login/ - вход
├── /profile/ - профиль
├── /logout/ - выход
├── /classroom-report/ - отчёт класса
└── admin пути
```

## Базы данных и модели
```
accounts.models:
├── CustomUser - расширенный User
│   ├── role
│   └── teacher_status
├── Achievement
│   ├── student (ForeignKey)
│   └── result (CharField)
└── Classroom
```

## Статические файлы
- CSS стили
- Изображения (hse.jpg, image-Photoroom-1.jpg)
- Логотипы и иконки

## Админ интерфейс
- Полная кастомизация Django Admin
- Фильтры и поиск по моделям
- Inline редактирование

## Отчёты
- Отчёты по классам
- Статистика достижений учеников
- Прогресс учащихся


## Дополнительный функционал
- Telegram бот интеграция (bot.py)
- Utils модуль (утилиты)
- Миграции Django
- Тесты (tests.py)
- Apps конфигурации
