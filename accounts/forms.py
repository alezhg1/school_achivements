# forms.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.safestring import mark_safe
from .models import CustomUser, Achievement, Classroom, Invitation


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Почта")
    class_number = forms.CharField(label="Класс (номер)", required=False)
    class_letter = forms.CharField(label="Буква", required=False)
    role = forms.ChoiceField(label="Роль", choices=(('student', 'Ученик'), ('teacher', 'Учитель')),
                             widget=forms.RadioSelect)
    accept_policy = forms.BooleanField(
        label=mark_safe('Согласен с <a href="/policy/" target="_blank">политикой обработки персональных данных</a>')
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email',
                  'class_number', 'class_letter',
                  'role', 'password1', 'password2', 'accept_policy')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем обязательность полей класса для учителей
        if 'role' in self.data and self.data['role'] == 'teacher':
            self.fields['class_number'].required = False
            self.fields['class_letter'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        role = self.cleaned_data.get('role')

        if role == 'teacher':
            if not email.endswith('@schmos444.ru'):
                raise forms.ValidationError("Для регистрации учителем используйте школьный домен @schmos444.ru")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        # Если это учитель, устанавливаем статус "ожидает подтверждения"
        if user.role == 'teacher':
            user.teacher_status = 'pending'
            user.is_active = True  # Аккаунт активен, но функциональность ограничена

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Логин или почта")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['title', 'description', 'image', 'result', 'year']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название мероприятия'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Короткое описание', 'rows': 4}),
            'result': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Год участия'}),
        }

    def clean_year(self):
        y = self.cleaned_data.get('year')
        if y:
            if y < 1900 or y > 2100:
                raise forms.ValidationError("Введите корректный год.")
        return y


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'description', 'grade']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Название класса в ГБОУ 444"


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['to_user']