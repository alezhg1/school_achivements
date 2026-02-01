from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
from accounts import views

import accounts.admin

urlpatterns = [
    path('admin/', accounts.admin.admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'
handler403 = 'accounts.views.custom_403'
handler400 = 'accounts.views.custom_400'
