from django.urls import path
from . import views
from django.conf import settings



urlpatterns = [
    # ------------------- Аутентификация -------------------
    path('register/', views.register, name='register'),
    path('policy/', views.policy_view, name='policy'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ------------------- Главные панели -------------------
    path('dashboard/', views.dashboard, name='dashboard'),  # для учеников
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),  # для учителей

    # ------------------- Классы -------------------
    path('teacher/classes/', views.teacher_classes, name='teacher_classes'),
    path('teacher/classes/create/', views.create_class, name='create_class'),
    path('teacher/classes/<int:class_id>/', views.class_detail, name='class_detail'),
    path('teacher/classes/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('teacher/classes/<int:class_id>/delete/', views.delete_class, name='delete_class'),
    path('teacher/classes/<int:class_id>/invite/', views.send_invitation, name='send_invite'),
    path('teacher/classes/<int:class_id>/remove/<int:student_id>/', views.remove_student, name='remove_student'),

    # ------------------- Приглашения -------------------
    path('invite/accept/<int:inv_id>/', views.accept_invitation, name='accept_invite'),
    path('api/search-users/', views.search_users_api, name='search_users_api'),

    # ------------------- Достижения -------------------
    path('achievement/add/', views.add_achievement, name='add_achievement'),
    path('achievement/add/<int:user_id>/', views.add_achievement, name='add_achievement_for'),
    # редактирование / удаление достижений
    path('achievement/<int:ach_id>/edit/', views.edit_achievement, name='edit_achievement'),
    path('achievement/<int:ach_id>/delete/', views.delete_achievement, name='delete_achievement'),

    path('teacher/classes/<int:class_id>/add-achievement/', views.add_achievement_from_class, name='add_achievement_from_class'),



    # ------------------- Профили -------------------
    path('profile/<str:username>/', views.profile_view, name='profile'),

    # ------------------- Уведомления -------------------
    path('notifications/', views.notifications_view, name='notifications'),

    # ------------------- FAQ -------------------
    path('faq/', views.faq, name='faq'),

    path('check-video/', views.check_video, name='check_video'),
]

handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'
