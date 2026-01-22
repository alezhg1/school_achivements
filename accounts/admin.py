from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Classroom, Achievement, Invitation, Notification
from django.contrib.auth.models import Group, Permission


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    #site_header = "🎓 Мой достижения 444"  # ← Заголовок вверху
    #site_title = "Admin | Достижения"  # ← Title браузера
    #index_title = "Добро пожаловать в админ!"

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'teacher_status', 'is_active')
    list_filter = ('role', 'teacher_status', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['approve_teachers', 'reject_teachers']

    fieldsets = UserAdmin.fieldsets + (
        ('🎓 Дополнительная информация', {
            'fields': ('role', 'teacher_status', 'school', 'class_number', 'class_letter')
        }),
    )

    def approve_teachers(self, request, queryset):
        """Одобрить заявки учителей"""
        teachers = queryset.filter(role='teacher', teacher_status='pending')
        count = teachers.update(teacher_status='approved')

        # Создаём уведомления для подтверждённых учителей
        for teacher in teachers:
            Notification.objects.create(
                user=teacher,
                text="🎉 Ваша заявка на регистрацию учителя одобрена! Теперь вы можете использовать все функции платформы.",
                link="/accounts/dashboard/"
            )

        self.message_user(request, f'✅ Одобрено {count} заявок учителей')

    approve_teachers.short_description = '✅ Одобрить заявки учителей'

    def reject_teachers(self, request, queryset):
        """Отклонить заявки учителей"""
        teachers = queryset.filter(role='teacher', teacher_status='pending')
        count = teachers.update(teacher_status='rejected')

        # Создаём уведомления для отклонённых
        for teacher in teachers:
            Notification.objects.create(
                user=teacher,
                text="😔 К сожалению, ваша заявка на регистрацию учителя была отклонена администратором.",
                link="/"
            )

        self.message_user(request, f'❌ Отклонено {count} заявок учителей')

    reject_teachers.short_description = '❌ Отклонить заявки учителей'


admin.site.register(Classroom)
admin.site.register(Achievement)
admin.site.register(Invitation)
admin.site.register(Notification)
