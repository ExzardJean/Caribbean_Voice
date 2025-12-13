from django import forms
from inventory.models import User
from django.contrib.auth.forms import UsernameField
from django.utils.translation import gettext_lazy as _

class UserProfileForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Nouveau mot de passe'), widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label=_('Confirmer le mot de passe'), widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'address', 'profile_image']
        field_classes = {'username': UsernameField}

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', _('Les mots de passe ne correspondent pas.'))
            if password1 and len(password1) < 6:
                self.add_error('password1', _('Le mot de passe doit contenir au moins 6 caractères.'))
        return cleaned_data
