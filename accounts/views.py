from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q
from .forms import RegisterForm, LoginForm, AchievementForm, ClassroomForm, InvitationForm
from .models import CustomUser, Classroom, Achievement, Invitation, Notification
import os
from django.conf import settings


def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Если это учитель, отправляем уведомление администраторам
            if user.role == 'teacher':
                # Получаем всех суперпользователей
                admins = CustomUser.objects.filter(is_superuser=True)
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        text=f"Новая заявка на регистрацию учителя: {user.username} ({user.email})",
                        link=f"/admin/accounts/customuser/{user.id}/change/"
                    )

                messages.success(
                    request,
                    'Регистрация прошла успешно! Ваша заявка отправлена администраторам на рассмотрение. '
                    'Вы получите уведомление, когда ваш аккаунт будет подтвержден.'
                )
            else:
                messages.success(request, 'Регистрация прошла успешно! Войдите в аккаунт.')

            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username_or_email, password=password)
            if not user:
                try:
                    u = CustomUser.objects.get(email=username_or_email)
                    user = authenticate(request, username=u.username, password=password)
                except CustomUser.DoesNotExist:
                    pass
            if user:
                # Проверяем, является ли пользователь неподтвержденным учителем
                if user.role == 'teacher' and user.teacher_status != 'approved':
                    messages.warning(
                        request,
                        'Ваша заявка еще не подтверждена администратором. '
                        'Вы получите уведомление, когда ваш аккаунт будет активирован.'
                    )
                    return redirect('home')

                login(request, user)
                return redirect('teacher_dashboard' if user.role == 'teacher' else 'dashboard')
            messages.error(request, 'Неверные данные для входа.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    achievements = request.user.achievements.all()
    invitations = request.user.invitations.filter(status='sent')
    return render(request, 'accounts/dashboard.html', {'achievements': achievements, 'invitations': invitations})


@login_required
def teacher_dashboard(request):
    if not request.user.is_approved_teacher():
        if request.user.role == 'teacher' and request.user.teacher_status == 'pending':
            messages.warning(
                request,
                'Ваша заявка еще не подтверждена администратором. '
                'Вы получите доступ к функциям учителя после подтверждения.'
            )
            return redirect('home')
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classes = Classroom.objects.filter(teacher=request.user)
    return render(request, 'accounts/teacher_dashboard.html', {'classes': classes})


@login_required
def teacher_classes(request):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classes = Classroom.objects.filter(teacher=request.user)
    return render(request, 'accounts/teacher_classes.html', {'classes': classes})


@login_required
def create_class(request):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    form = ClassroomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        classroom = form.save(commit=False)
        classroom.teacher = request.user
        # Школа автоматически ГБОУ 444
        classroom.save()
        messages.success(request, 'Класс успешно создан в ГБОУ 444!')
        return redirect('teacher_classes')
    return render(request, 'accounts/create_class.html', {'form': form})


@login_required
def class_detail(request, class_id):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    students = classroom.students.all()

    # Вычисляем статистику
    total_achievements = Achievement.objects.filter(student__in=students).count()
    avg_achievements = students.count() and round(total_achievements / students.count(), 1) or 0
    active_students = students.count() and round(
        (students.filter(achievements__isnull=False).distinct().count() / students.count()) * 100) or 0

    return render(request, 'accounts/class_detail.html', {
        'classroom': classroom,
        'students': students,
        'total_achievements': total_achievements,
        'avg_achievements': avg_achievements,
        'active_students': active_students
    })


@login_required
def edit_class(request, class_id):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    form = ClassroomForm(request.POST or None, instance=classroom)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Изменения сохранены.')
        return redirect('class_detail', class_id=classroom.id)
    return render(request, 'accounts/edit_class.html', {'form': form, 'classroom': classroom})


@login_required
def delete_class(request, class_id):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    classroom.delete()
    messages.warning(request, f'Класс "{classroom.name}" удалён.')
    return redirect('teacher_classes')


@login_required
def remove_student(request, class_id, student_id):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    student = get_object_or_404(CustomUser, id=student_id)
    classroom.students.remove(student)
    Notification.objects.create(user=student, text=f"Вы были удалены из класса {classroom.name}")
    messages.info(request, f"Ученик {student.username} удалён из {classroom.name}")
    return redirect('class_detail', class_id=class_id)


@login_required
def send_invitation(request, class_id):
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)
    form = InvitationForm(request.POST or None)

    # Статистика для шаблона
    invitations = classroom.invitations.all()
    accepted_invitations = invitations.filter(status='accepted').count()
    pending_invitations = invitations.filter(status='sent').count()

    if request.method == 'POST' and form.is_valid():
        inv = form.save(commit=False)
        inv.classroom = classroom
        inv.from_user = request.user
        inv.save()
        Notification.objects.create(
            user=inv.to_user,
            text=f"Вас пригласили в класс {classroom.name}",
            link="/accounts/notifications/"
        )
        messages.success(request, 'Приглашение отправлено!')
        return redirect('teacher_classes')

    return render(request, 'accounts/send_invite.html', {
        'form': form,
        'classroom': classroom,
        'accepted_invitations': accepted_invitations,
        'pending_invitations': pending_invitations
    })


@login_required
def accept_invitation(request, inv_id):
    inv = get_object_or_404(Invitation, id=inv_id, to_user=request.user)
    inv.status = 'accepted'
    inv.classroom.students.add(request.user)
    inv.save()
    Notification.objects.create(
        user=inv.from_user,
        text=f"{request.user.username} принял приглашение в {inv.classroom.name}"
    )
    messages.success(request, 'Вы присоединились к классу!')
    return redirect('dashboard')


@login_required
def add_achievement(request, user_id=None):
    """
    Добавление достижения. Если user_id указан и текущий user — учитель, то добавляем ученику.
    Если user_id не указан — добавляем для себя (current user).
    """
    if user_id:
        # teacher adds to student
        if not request.user.is_approved_teacher():
            return HttpResponseForbidden("Только подтвержденный учитель может добавлять достижения другим.")
        target = get_object_or_404(CustomUser, id=user_id)
    else:
        target = request.user

    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            ach = form.save(commit=False)
            ach.student = target
            ach.added_by = request.user
            ach.save()
            messages.success(request, 'Достижение успешно добавлено.')
            return redirect('profile', username=target.username)
    else:
        form = AchievementForm()

    return render(request, 'accounts/add_achievement.html', {'form': form, 'target': target})


@login_required
def edit_achievement(request, ach_id):
    """
    Редактирование достижения. Можно редактировать только если вы — владелец (student).
    """
    ach = get_object_or_404(Achievement, id=ach_id)
    # только владелец (student) может редактировать своё достижение
    if request.user != ach.student:
        return HttpResponseForbidden("Вы можете редактировать только свои достижения.")

    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES, instance=ach)
        if form.is_valid():
            form.save()
            messages.success(request, 'Достижение обновлено.')
            return redirect('profile', username=request.user.username)
    else:
        form = AchievementForm(instance=ach)

    return render(request, 'accounts/edit_achievement.html', {'form': form, 'achievement': ach})


@login_required
def delete_achievement(request, ach_id):
    """
    Удаление достижения (POST). Только владелец может удалить.
    """
    ach = get_object_or_404(Achievement, id=ach_id)
    if request.user != ach.student:
        return HttpResponseForbidden("Удалять можно только свои достижения.")

    if request.method == 'POST':
        ach.delete()
        messages.success(request, 'Достижение удалено.')
        return redirect('profile', username=request.user.username)
    else:
        # если попытка GET — показываем страницу с подтверждением (или 405)
        # но проще: редирект назад с сообщением
        messages.error(request, 'Для удаления используйте кнопку "Удалить" и подтвердите действие.')
        return redirect('profile', username=request.user.username)


def profile_view(request, username):
    """
    Просмотр профиля пользователя. Показываем таблицу достижений (с фильтрами на клиенте)
    и "значки" (блоки).
    """
    profile_user = get_object_or_404(CustomUser, username=username)
    achievements = Achievement.objects.filter(student=profile_user).order_by('-created_at')

    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'achievements': achievements
    })


@login_required
def notifications_view(request):
    notes = request.user.notifications.order_by('-created_at')
    for n in notes:
        n.read = True
        n.save()
    return render(request, 'accounts/notifications.html', {'notifications': notes})


@login_required
def add_achievement_from_class(request, class_id):
    """
    Добавление достижения ученику из страницы класса
    """
    if not request.user.is_approved_teacher():
        return HttpResponseForbidden("Доступ только для подтвержденных учителей.")

    classroom = get_object_or_404(Classroom, id=class_id, teacher=request.user)

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if not student_id:
            messages.error(request, 'Пожалуйста, выберите ученика')
            return redirect('class_detail', class_id=class_id)

        try:
            student = CustomUser.objects.get(id=student_id)
            # Проверяем, что ученик действительно в этом классе
            if student not in classroom.students.all():
                messages.error(request, 'Этот ученик не состоит в вашем классе')
                return redirect('class_detail', class_id=class_id)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Ученик не найден')
            return redirect('class_detail', class_id=class_id)

        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            ach = form.save(commit=False)
            ach.student = student
            ach.added_by = request.user
            ach.save()
            messages.success(request, f'Достижение успешно добавлено ученику {student.get_full_name()}')
            return redirect('class_detail', class_id=class_id)
        else:
            # Если форма невалидна, показываем ошибки
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        messages.error(request, 'Неверный метод запроса')

    return redirect('class_detail', class_id=class_id)


@login_required
def search_users_api(request):
    """
    API для поиска пользователей по имени, фамилии или логину
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse([], safe=False)

    try:
        # Ищем пользователей (только учеников)
        users = CustomUser.objects.filter(
            Q(role='student') &
            (Q(username__icontains=query) |
             Q(first_name__icontains=query) |
             Q(last_name__icontains=query))
        ).exclude(id=request.user.id)[:10]  # Ограничиваем результаты

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'class_number': user.class_number or '',
                'class_letter': user.class_letter or '',
            })

        return JsonResponse(users_data, safe=False)

    except Exception as e:
        print(f"Error in search_users_api: {e}")
        return JsonResponse([], safe=False)


def check_video(request):
    """Временная view для проверки видео"""
    video_path = os.path.join(settings.BASE_DIR, 'static', 'videos', '404-bg.mp4')

    if os.path.exists(video_path):
        return HttpResponse(f"✅ Видео найдено: {video_path}<br>Размер: {os.path.getsize(video_path)} байт")
    else:
        return HttpResponse(f"❌ Видео не найдено: {video_path}")


def custom_404(request, exception=None):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)


def custom_403(request, exception=None):
    """Кастомная страница 403 (Доступ запрещен)"""
    return render(request, '403.html', status=403)


def custom_400(request, exception=None):
    """Кастомная страница 400 (Неверный запрос)"""
    return render(request, '400.html', status=400)


def policy_view(request):
    """Страница политики обработки персональных данных"""
    return render(request, 'policy.html')


@login_required
def teacher_status_check(request):
    """
    Страница проверки статуса учителя для неподтвержденных учителей
    """
    if request.user.role != 'teacher' or request.user.teacher_status == 'approved':
        return redirect('dashboard')

    return render(request, 'accounts/teacher_status_check.html', {
        'teacher_status': request.user.teacher_status
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def faq(request):
    """Страница FAQ с часто задаваемыми вопросами"""
    context = {
        'page_title': 'FAQ - Часто задаваемые вопросы',
    }
    return render(request, 'accounts/faq.html', context)
