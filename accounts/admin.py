from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
import csv
from .models import CustomUser, Classroom, Achievement, Invitation, Notification
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.utils.safestring import mark_safe

TEACHER_STATUS_CHOICES = (
    ('pending', 'Ожидает подтверждения'),
    ('approved', 'Подтвержден'),
    ('rejected', 'Отклонен'),
)


class MyAdminSite(admin.AdminSite):
    site_header = "🎓 Панель управления - ГБОУ 444"
    site_title = "Мои достижения - Администрирование"
    index_title = "📊 Обзор системы"

    # Кастомные стили для всей админки
    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = """
        <style>
            :root {
                --primary: #4361ee;
                --primary-dark: #3a56d4;
                --secondary: #7209b7;
                --success: #4cc9f0;
                --warning: #f72585;
                --info: #4895ef;
                --light: #f8f9fa;
                --dark: #212529;
                --sidebar: #2d3748;
                --sidebar-hover: #4a5568;
            }

            /* Основные стили */
            #header {
                background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
                color: white !important;
            }

            .module h2, .module caption {
                background: linear-gradient(135deg, var(--primary) 0%, var(--info) 100%) !important;
                color: white !important;
                border-radius: 8px 8px 0 0;
            }

            .dashboard .module table {
                border-radius: 0 0 8px 8px;
                overflow: hidden;
            }

            /* Кнопки */
            .button, input[type=submit], input[type=button], .submit-row input {
                background: var(--primary) !important;
                border: none !important;
                border-radius: 6px !important;
                transition: all 0.3s ease !important;
            }

            .button:hover, input[type=submit]:hover, input[type=button]:hover {
                background: var(--primary-dark) !important;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
            }

            /* Бейджи */
            .badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .badge-success { background: #10b981; color: white; }
            .badge-warning { background: #f59e0b; color: white; }
            .badge-danger { background: #ef4444; color: white; }
            .badge-info { background: #3b82f6; color: white; }
            .badge-secondary { background: #6b7280; color: white; }

            /* Карточки статистики */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }

            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border-left: 4px solid var(--primary);
                transition: transform 0.3s ease;
            }

            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            }

            .stat-number {
                font-size: 2rem;
                font-weight: bold;
                color: var(--primary);
                margin-bottom: 5px;
            }

            .stat-label {
                color: #6b7280;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            /* Списки */
            .recent-list {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }

            .recent-list h3 {
                margin-top: 0;
                color: var(--primary);
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 10px;
            }

            .recent-item {
                padding: 12px 0;
                border-bottom: 1px solid #f3f4f6;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .recent-item:last-child {
                border-bottom: none;
            }

            /* Таблицы */
            #changelist .results {
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }

            #changelist table thead th {
                background: linear-gradient(135deg, var(--primary) 0%, var(--info) 100%) !important;
                color: white !important;
                border: none !important;
            }

            #changelist table tbody tr:hover {
                background: #f8fafc !important;
            }

            /* Формы */
            .form-row {
                padding: 15px;
                margin-bottom: 10px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }

            /* Действия */
            .action-buttons {
                display: flex;
                gap: 5px;
                flex-wrap: wrap;
            }

            .action-btn {
                padding: 6px 12px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
            }

            .action-btn.approve {
                background: #10b981;
                color: white;
            }

            .action-btn.reject {
                background: #ef4444;
                color: white;
            }

            .action-btn.report {
                background: #3b82f6;
                color: white;
            }

            .action-btn.csv {
                background: #8b5cf6;
                color: white;
            }

            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
        </style>
        """
        return context

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reports/student/<int:user_id>/', self.admin_view(self.student_report), name='student_report'),
            path('reports/classroom/<int:class_id>/', self.admin_view(self.classroom_report), name='classroom_report'),
            path('reports/export-student-csv/<int:user_id>/', self.admin_view(self.export_student_csv),
                 name='export_student_csv'),
            path('reports/export-classroom-csv/<int:class_id>/', self.admin_view(self.export_classroom_csv),
                 name='export_classroom_csv'),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        # Статистика пользователей
        total_users = CustomUser.objects.count()
        teachers_count = CustomUser.objects.filter(role='teacher').count()
        students_count = CustomUser.objects.filter(role='student').count()

        # Статистика заявок учителей
        pending_teachers = CustomUser.objects.filter(role='teacher', teacher_status='pending').count()
        approved_teachers = CustomUser.objects.filter(role='teacher', teacher_status='approved').count()
        rejected_teachers = CustomUser.objects.filter(role='teacher', teacher_status='rejected').count()

        # Статистика достижений
        total_achievements = Achievement.objects.count()
        week_ago = timezone.now() - timedelta(days=7)
        recent_achievements = Achievement.objects.filter(created_at__gte=week_ago).count()

        # Статистика классов
        total_classes = Classroom.objects.count()
        active_classes = Classroom.objects.annotate(student_count=Count('students')).filter(student_count__gt=0).count()

        # Последние пользователи
        latest_users = CustomUser.objects.order_by('-date_joined')[:8]

        # Последние достижения
        latest_achievements = Achievement.objects.select_related('student').order_by('-created_at')[:8]

        # Последние заявки учителей
        latest_teacher_requests = CustomUser.objects.filter(
            role='teacher',
            teacher_status='pending'
        ).order_by('-date_joined')[:5]

        extra_context = extra_context or {}
        extra_context.update({
            'total_users': total_users,
            'teachers_count': teachers_count,
            'students_count': students_count,
            'pending_teachers': pending_teachers,
            'approved_teachers': approved_teachers,
            'rejected_teachers': rejected_teachers,
            'total_achievements': total_achievements,
            'recent_achievements': recent_achievements,
            'total_classes': total_classes,
            'active_classes': active_classes,
            'latest_users': latest_users,
            'latest_achievements': latest_achievements,
            'latest_teacher_requests': latest_teacher_requests,
        })

        return super().index(request, extra_context)

    def student_report(self, request, user_id):
        student = get_object_or_404(CustomUser, id=user_id, role='student')
        achievements = Achievement.objects.filter(student=student).order_by('-created_at')
        stats = student.get_achievements_stats()

        context = {
            'student': student,
            'achievements': achievements,
            'stats': stats,
            'title': f'Отчет по ученику: {student.get_full_name() or student.username}'
        }
        return render(request, 'admin/reports/student_report.html', context)

    def classroom_report(self, request, class_id):
        classroom = get_object_or_404(Classroom, id=class_id)
        stats = classroom.get_class_stats()
        students = classroom.students.all().annotate(
            achievement_count=Count('achievements')
        ).order_by('-achievement_count')

        context = {
            'classroom': classroom,
            'students': students,
            'stats': stats,
            'title': f'Отчет по классу: {classroom.name}'
        }
        return render(request, 'admin/reports/classroom_report.html', context)

    def export_student_csv(self, request, user_id):
        student = get_object_or_404(CustomUser, id=user_id, role='student')
        achievements = Achievement.objects.filter(student=student).order_by('-created_at')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="student_{student.username}_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Отчет по ученику', f'{student.get_full_name() or student.username}'])
        writer.writerow(['Школа', student.school])
        writer.writerow(['Класс', f'{student.class_number}{student.class_letter}'])
        writer.writerow([])
        writer.writerow(['Название мероприятия', 'Результат', 'Год', 'Дата добавления', 'Описание'])

        for achievement in achievements:
            writer.writerow([
                achievement.title,
                achievement.get_result_display(),
                achievement.year or '',
                achievement.created_at.strftime('%d.%m.%Y'),
                achievement.description[:100] + '...' if len(achievement.description) > 100 else achievement.description
            ])

        return response

    def export_classroom_csv(self, request, class_id):
        classroom = get_object_or_404(Classroom, id=class_id)
        students = classroom.students.all().annotate(
            achievement_count=Count('achievements')
        ).order_by('-achievement_count')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="class_{classroom.name}_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Отчет по классу', classroom.name])
        writer.writerow(['Учитель', classroom.teacher.get_full_name() or classroom.teacher.username])
        writer.writerow(['Всего учеников', students.count()])
        writer.writerow([])
        writer.writerow(['Ученик', 'Количество достижений', 'Класс', 'Последнее достижение'])

        for student in students:
            last_achievement = student.achievements.order_by('-created_at').first()
            writer.writerow([
                student.get_full_name() or student.username,
                student.achievement_count,
                f'{student.class_number}{student.class_letter}',
                last_achievement.created_at.strftime('%d.%m.%Y') if last_achievement else 'Нет достижений'
            ])

        return response


# Создаем экземпляр кастомного админ-сайта
my_admin_site = MyAdminSite(name='myadmin')


# ====== БАЗОВЫЕ АДМИН-КЛАССЫ ======
@admin.register(CustomUser, site=my_admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'teacher_status_badge',
                    'school_class', 'achievements_count', 'is_active', 'date_joined', 'admin_actions')
    list_filter = ('role', 'teacher_status', 'is_active', 'is_staff', 'date_joined', 'school')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['generate_student_report', 'approve_teachers', 'reject_teachers']
    list_per_page = 25

    fieldsets = UserAdmin.fieldsets + (
        ('🎓 Дополнительная информация', {
            'fields': ('role', 'teacher_status', 'school', 'class_number', 'class_letter')
        }),
    )

    def full_name(self, obj):
        name = obj.get_full_name()
        return name if name else format_html('<span style="color: #6b7280;">—</span>')

    full_name.short_description = '👤 ФИО'

    def teacher_status_badge(self, obj):
        if obj.role != 'teacher':
            return format_html('<span style="color: #6b7280;">—</span>')

        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }
        color = colors.get(obj.teacher_status, 'secondary')
        icon = icons.get(obj.teacher_status, '❓')
        status_display = dict(TEACHER_STATUS_CHOICES).get(obj.teacher_status, obj.teacher_status)

        return format_html(
            '<span class="badge badge-{}">{} {}</span>',
            color, icon, status_display
        )

    teacher_status_badge.short_description = '📋 Статус учителя'

    def school_class(self, obj):
        if obj.class_number and obj.class_letter:
            return format_html(
                '<span style="background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 12px; font-weight: 500;">{}{}</span>',
                obj.class_number, obj.class_letter
            )
        return format_html('<span style="color: #6b7280;">—</span>')

    school_class.short_description = '🏫 Класс'

    def achievements_count(self, obj):
        if obj.role == 'student':
            count = obj.achievements.count()
            color = '#10b981' if count > 0 else '#6b7280'
            return format_html(
                '<span style="color: {}; font-weight: 600;">{}</span>',
                color, count
            )
        return format_html('<span style="color: #6b7280;">—</span>')

    achievements_count.short_description = '🏆 Достижений'

    def generate_student_report(self, request, queryset):
        for student in queryset.filter(role='student'):
            self.message_user(
                request,
                f'📊 Отчет для {student.username} доступен по ссылке в списке действий',
                level='INFO'
            )

    generate_student_report.short_description = '📊 Создать отчет для выбранных учеников'

    def approve_teachers(self, request, queryset):
        teachers = queryset.filter(role='teacher', teacher_status='pending')
        count = teachers.count()

        for teacher in teachers:
            teacher.teacher_status = 'approved'
            teacher.save()

            # Отправляем уведомление учителю
            Notification.objects.create(
                user=teacher,
                text="🎉 Ваша заявка на регистрацию учителя одобрена! Теперь вы можете использовать все функции платформы.",
                link="/accounts/dashboard/"
            )

        self.message_user(
            request,
            f'✅ Успешно одобрено {count} заявок учителей. Пользователи получили уведомления.',
            level='SUCCESS'
        )

    approve_teachers.short_description = '✅ Одобрить выбранные заявки учителей'

    def reject_teachers(self, request, queryset):
        teachers = queryset.filter(role='teacher', teacher_status='pending')
        count = teachers.count()

        for teacher in teachers:
            teacher.teacher_status = 'rejected'
            teacher.save()

            # Отправляем уведомление учителю
            Notification.objects.create(
                user=teacher,
                text="😔 К сожалению, ваша заявка на регистрацию учителя была отклонена администратором.",
                link="/"
            )

        self.message_user(
            request,
            f'❌ Отклонено {count} заявок учителей. Пользователи получили уведомления.',
            level='WARNING'
        )

    reject_teachers.short_description = '❌ Отклонить выбранные заявки учителей'

    def admin_actions(self, obj):
        actions = []

        if obj.role == 'student':
            actions.append(
                format_html(
                    '<a href="{}" class="action-btn report" title="Просмотр отчета">📊</a>',
                    f'/admin/reports/student/{obj.id}/'
                )
            )
            actions.append(
                format_html(
                    '<a href="{}" class="action-btn csv" title="Экспорт в CSV">📥</a>',
                    f'/admin/reports/export-student-csv/{obj.id}/'
                )
            )
        elif obj.role == 'teacher' and obj.teacher_status == 'pending':
            actions.append(
                format_html(
                    '<a href="?_selected_action={}&action=approve_teachers" class="action-btn approve" title="Одобрить заявку">✅</a>',
                    obj.id
                )
            )
            actions.append(
                format_html(
                    '<a href="?_selected_action={}&action=reject_teachers" class="action-btn reject" title="Отклонить заявку">❌</a>',
                    obj.id
                )
            )
        else:
            return format_html('<span style="color: #6b7280;">—</span>')

        return format_html('<div class="action-buttons">{}</div>', mark_safe(''.join(actions)))

    admin_actions.short_description = '⚡ Действия'


@admin.register(Achievement, site=my_admin_site)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'result_badge', 'year', 'added_by', 'created_at_badge')
    list_filter = ('result', 'year', 'created_at')
    search_fields = ('title', 'student__username', 'description')
    readonly_fields = ('created_at',)
    list_per_page = 25

    def get_list_display(self, request):
        return ['title', 'student', 'result_badge', 'year', 'added_by', 'created_at_badge']

    def result_badge(self, obj):
        colors = {
            'Победитель': 'success',
            'Призёр': 'warning',
            'Участник': 'info',
            'Другое': 'secondary'
        }
        icons = {
            'Победитель': '🥇',
            'Призёр': '🥈',
            'Участник': '🎯',
            'Другое': '📝'
        }
        color = colors.get(obj.result, 'secondary')
        icon = icons.get(obj.result, '📝')
        return format_html(
            '<span class="badge badge-{}">{} {}</span>',
            color, icon, obj.get_result_display()
        )

    result_badge.short_description = '🏅 Результат'

    def created_at_badge(self, obj):
        days_ago = (timezone.now() - obj.created_at).days
        if days_ago == 0:
            return format_html('<span style="color: #10b981;">Сегодня</span>')
        elif days_ago == 1:
            return format_html('<span style="color: #10b981;">Вчера</span>')
        elif days_ago < 7:
            return format_html('<span style="color: #3b82f6;">{} дн. назад</span>', days_ago)
        else:
            return format_html('<span style="color: #6b7280;">{}</span>', obj.created_at.strftime('%d.%m.%Y'))

    created_at_badge.short_description = '📅 Добавлено'


@admin.register(Classroom, site=my_admin_site)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_badge', 'grade', 'teacher', 'students_count',
                    'achievements_count', 'created_at_badge', 'admin_actions')
    list_filter = ('school', 'grade')
    search_fields = ('name', 'teacher__username')
    filter_horizontal = ('students',)
    list_per_page = 20

    def school_badge(self, obj):
        return format_html(
            '<span style="background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">🏫 {}</span>',
            obj.school
        )

    school_badge.short_description = '🏢 Школа'

    def students_count(self, obj):
        count = obj.students.count()
        return format_html(
            '<span style="color: #0369a1; font-weight: 600;">👥 {}</span>',
            count
        )

    students_count.short_description = '👥 Учеников'

    def achievements_count(self, obj):
        count = Achievement.objects.filter(student__in=obj.students.all()).count()
        color = '#10b981' if count > 0 else '#6b7280'
        return format_html(
            '<span style="color: {}; font-weight: 600;">🏆 {}</span>',
            color, count
        )

    achievements_count.short_description = '🏆 Достижений'

    def created_at_badge(self, obj):
        return format_html(
            '<span style="color: #6b7280; font-size: 12px;">{}</span>',
            obj.created_at.strftime('%d.%m.%Y')
        )

    created_at_badge.short_description = '📅 Создан'

    def admin_actions(self, obj):
        return format_html(
            '<div class="action-buttons">'
            '<a href="{}" class="action-btn report" title="Просмотр отчета">📊</a>'
            '<a href="{}" class="action-btn csv" title="Экспорт в CSV">📥</a>'
            '</div>',
            f'/admin/reports/classroom/{obj.id}/',
            f'/admin/reports/export-classroom-csv/{obj.id}/'
        )

    admin_actions.short_description = '⚡ Действия'


@admin.register(Invitation, site=my_admin_site)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'to_user', 'from_user', 'status_badge', 'created_at_badge')
    list_filter = ('status', 'created_at')
    search_fields = ('to_user__username', 'classroom__name')
    list_per_page = 20

    def status_badge(self, obj):
        colors = {
            'sent': 'warning',
            'accepted': 'success',
            'declined': 'danger'
        }
        icons = {
            'sent': '📤',
            'accepted': '✅',
            'declined': '❌'
        }
        color = colors.get(obj.status, 'secondary')
        icon = icons.get(obj.status, '❓')
        return format_html(
            '<span class="badge badge-{}">{} {}</span>',
            color, icon, obj.get_status_display()
        )

    status_badge.short_description = '📋 Статус'

    def created_at_badge(self, obj):
        return format_html(
            '<span style="color: #6b7280; font-size: 12px;">{}</span>',
            obj.created_at.strftime('%d.%m.%Y')
        )

    created_at_badge.short_description = '📅 Отправлено'


@admin.register(Notification, site=my_admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'text_preview', 'read_badge', 'created_at_badge')
    list_filter = ('read', 'created_at')
    search_fields = ('user__username', 'text')
    list_per_page = 20

    def text_preview(self, obj):
        text = obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
        return format_html(
            '<span style="font-weight: 500;">{}</span>',
            text
        )

    text_preview.short_description = '💬 Текст'

    def read_badge(self, obj):
        if obj.read:
            return format_html(
                '<span class="badge badge-success">✅ Прочитано</span>'
            )
        return format_html(
            '<span class="badge badge-warning">📬 Не прочитано</span>'
        )

    read_badge.short_description = '📭 Статус'

    def created_at_badge(self, obj):
        return format_html(
            '<span style="color: #6b7280; font-size: 12px;">{}</span>',
            obj.created_at.strftime('%d.%m.%Y %H:%M')
        )

    created_at_badge.short_description = '📅 Время'


# Регистрируем стандартные модели
my_admin_site.register(Group)
my_admin_site.register(Permission)