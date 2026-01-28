# accounts/media_serve_middleware.py
import os
from django.http import FileResponse, Http404
from django.conf import settings


class MediaServeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем, является ли запрос к медиафайлам
        if request.path.startswith(settings.MEDIA_URL):
            # Получаем путь к файлу
            file_path = os.path.join(settings.MEDIA_ROOT, request.path.replace(settings.MEDIA_URL, '', 1))

            # Проверяем существование файла
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Возвращаем файл
                return FileResponse(open(file_path, 'rb'))
            else:
                # Файл не найден
                raise Http404("Файл не найден")

        return self.get_response(request)