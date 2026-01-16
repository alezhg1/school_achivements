import time
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger('accounts.security')


class DDoSProtectionMiddleware:
    """
    Middleware для защиты от DDoS атак
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.request_times = {}

    def __call__(self, request):
        if not getattr(settings, 'DDoS_PROTECTION_ENABLED', True):
            return self.get_response(request)

        client_ip = self.get_client_ip(request)

        # Проверка частоты запросов
        if self.is_ddos_attack(client_ip):
            logger.warning(f"DDoS protection triggered for IP: {client_ip}")
            return HttpResponseForbidden("Слишком много запросов. Пожалуйста, попробуйте позже.")

        # Проверка concurrent запросов
        if self.has_too_many_concurrent_requests(client_ip):
            logger.warning(f"Too many concurrent requests from IP: {client_ip}")
            return HttpResponseForbidden("Слишком много одновременных запросов.")

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """Получение реального IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_ddos_attack(self, client_ip):
        """Проверка на DDoS атаку по частоте запросов"""
        now = time.time()
        cache_key = f"request_times_{client_ip}"

        # Получаем историю запросов
        request_times = cache.get(cache_key, [])

        # Удаляем старые записи (старше 1 минуты)
        request_times = [t for t in request_times if now - t < 60]

        # Проверяем лимит запросов в минуту
        max_requests = getattr(settings, 'MAX_REQUESTS_PER_MINUTE', 60)
        if len(request_times) >= max_requests:
            return True

        # Добавляем текущий запрос
        request_times.append(now)
        cache.set(cache_key, request_times, 60)  # Храним 1 минуту

        return False

    def has_too_many_concurrent_requests(self, client_ip):
        """Проверка на слишком много одновременных запросов"""
        cache_key = f"concurrent_requests_{client_ip}"
        current_requests = cache.get(cache_key, 0)

        max_concurrent = getattr(settings, 'MAX_CONCURRENT_REQUESTS', 50)
        if current_requests >= max_concurrent:
            return True

        # Увеличиваем счетчик
        cache.set(cache_key, current_requests + 1, 30)  # 30 секунд таймаут
        return False


class RateLimitMiddleware:
    """
    Middleware для ограничения частоты запросов
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = self.get_client_ip(request)

        # Особые лимиты для API endpoints
        if request.path.startswith('/accounts/api/'):
            if self.is_rate_limited(client_ip, 'api', 30, 300):  # 30/5min
                return JsonResponse({
                    'error': 'Превышен лимит запросов к API'
                }, status=429)

        # Лимиты для поиска пользователей
        elif request.path.startswith('/accounts/api/search-users/'):
            if self.is_rate_limited(client_ip, 'search', 10, 60):  # 10/min
                return JsonResponse({
                    'error': 'Слишком много поисковых запросов'
                }, status=429)

        # Лимиты для логина
        elif request.path == '/accounts/login/' and request.method == 'POST':
            if self.is_rate_limited(client_ip, 'login', 5, 60):  # 5/min
                return JsonResponse({
                    'error': 'Слишком много попыток входа'
                }, status=429)

        # Лимиты для регистрации
        elif request.path == '/accounts/register/' and request.method == 'POST':
            if self.is_rate_limited(client_ip, 'register', 3, 300):  # 3/5min
                return JsonResponse({
                    'error': 'Слишком много попыток регистрации'
                }, status=429)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_rate_limited(self, client_ip, action, max_requests, time_window):
        """Проверка ограничения частоты запросов"""
        cache_key = f"rate_limit_{action}_{client_ip}"
        now = time.time()

        # Получаем историю запросов
        request_history = cache.get(cache_key, [])

        # Удаляем старые записи
        request_history = [t for t in request_history if now - t < time_window]

        # Проверяем лимит
        if len(request_history) >= max_requests:
            return True

        # Добавляем текущий запрос
        request_history.append(now)
        cache.set(cache_key, request_history, time_window)

        return False