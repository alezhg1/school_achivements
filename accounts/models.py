from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

ROLE_CHOICES = (
    ('student', 'Ученик'),
    ('teacher', 'Учитель'),
)

TEACHER_STATUS_CHOICES = (
    ('pending', 'Ожидает подтверждения'),
    ('approved', 'Подтвержден'),
    ('rejected', 'Отклонен'),
)


class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    school = models.CharField("Школа", max_length=255, blank=True, default="ГБОУ 444")
    class_number = models.CharField("Класс", max_length=10, blank=True)
    class_letter = models.CharField("Буква", max_length=5, blank=True)
    teacher_status = models.CharField(  # ДОБАВИТЬ ЭТО ПОЛЕ
        max_length=20,
        choices=TEACHER_STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_approved_teacher(self):
        return self.role == 'teacher' and self.teacher_status == 'approved'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'




class Classroom(models.Model):
    name = models.CharField("Название класса", max_length=150)
    description = models.TextField("Описание", blank=True)
    school = models.CharField("Учреждение", max_length=255, blank=True, default="ГБОУ 444")
    grade = models.CharField("Класс", max_length=10)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_classes')
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='student_classes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (ГБОУ 444, {self.grade})"

    def get_class_stats(self):
        """Статистика по классу"""
        students = self.students.all()
        achievements = Achievement.objects.filter(student__in=students)

        total_achievements = achievements.count()
        avg_per_student = students.count() and round(total_achievements / students.count(), 1) or 0

        # Активные ученики (хотя бы 1 достижение)
        active_students = students.filter(achievements__isnull=False).distinct().count()
        active_percentage = students.count() and round((active_students / students.count()) * 100) or 0

        # Распределение по результатам
        result_stats = achievements.values('result').annotate(
            count=models.Count('id')
        ).order_by('-count')

        # Топ учеников
        top_students = students.annotate(
            achievement_count=models.Count('achievements')
        ).order_by('-achievement_count')[:5]

        return {
            'total_students': students.count(),
            'total_achievements': total_achievements,
            'avg_per_student': avg_per_student,
            'active_students': active_students,
            'active_percentage': active_percentage,
            'result_stats': result_stats,
            'top_students': top_students,
            'recent_achievements': achievements.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
        }



class Achievement(models.Model):
    RESULT_CHOICES = [
        ('Победитель', 'Победитель'),
        ('Призёр', 'Призёр'),
        ('Участник', 'Участник'),
        ('Другое', 'Другое'),
    ]

    title = models.CharField("Название мероприятия", max_length=255)
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Фото / грамота", upload_to='achievements/', blank=True, null=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='achievements', on_delete=models.CASCADE, verbose_name="Ученик")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='added_achievements', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Кто добавил")
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    year = models.PositiveIntegerField("Год", null=True, blank=True)
    result = models.CharField("Результат", max_length=32, choices=RESULT_CHOICES, default='Участник')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"

    def __str__(self):
        return f"{self.title} — {self.student}"

class Invitation(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='invitations')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    status = models.CharField(
        max_length=10,
        choices=(
            ('sent', 'Отправлено'),
            ('accepted', 'Принято'),
            ('declined', 'Отклонено')
        ),
        default='sent'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Приглашение {self.classroom} → {self.to_user}"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    text = models.CharField("Текст уведомления", max_length=255)
    link = models.CharField("Ссылка", max_length=255, blank=True)
    read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Уведомление {self.user}: {self.text[:40]}"