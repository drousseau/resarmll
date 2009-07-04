# -*- coding: utf-8 -*-
from django import forms
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from resarmll import settings
from resarmll.resa.models import Country, Badge
from models import GENDER_CHOICES

_attrs = { 'class': 'text', 'size': 30}
_attrs_passwd = { 'class': 'text', 'size': 30, 'autocomplete': 'off'}

class UserForm(forms.Form):
    username = forms.CharField(label=_(u"Username:"),
        max_length=28, min_length=3, widget=forms.TextInput(attrs=_attrs),
        #help_text=_(u"help")
        )
    password = forms.CharField(label=_(u"Password:"),
        min_length=5, max_length=32, widget=forms.PasswordInput(attrs=_attrs_passwd,
        render_value=False),
        help_text=_(u"The password must contain at least 5 characters."),
        )
    password_confirm = forms.CharField(label=_(u"Confirm password:"),
        min_length=5, max_length=32,
        widget=forms.PasswordInput(attrs=_attrs_passwd, render_value=False))
    email = forms.EmailField(label=_(u"E-mail address:"),
        max_length=64, widget=forms.TextInput(attrs=_attrs))
    gender = forms.ChoiceField(label=_(u"Gender:"), choices=GENDER_CHOICES, required=False,
        help_text=_(u"The Gender is not mandatory but could be useful for room distribution."),
        )
    last_name = forms.CharField(label=_(u"Last name:"),
        max_length=64, min_length=3, widget=forms.TextInput(attrs=_attrs))
    first_name = forms.CharField(label=_(u"First name:"),
        max_length=64, min_length=3, widget=forms.TextInput(attrs=_attrs))
    address = forms.CharField(label=_(u"Address:"), required=False,
        widget=forms.Textarea(attrs=_attrs),
        help_text=_(u"Address is useful for speakers or people who'll get a refund."),
        )
    language = forms.ChoiceField(label=_(u"Language:"),
        choices=settings.LANGUAGES)
    country = forms.ModelChoiceField(label=_(u"Country:"),
        queryset=Country.objects.all(), widget=forms.Select(), empty_label=None)
    badge_text = forms.CharField(label=_(u"Badge text:"),
        required=False, max_length=32, widget=forms.TextInput(attrs=_attrs),
        help_text=_(u"Free text printed on your badge (should not be too long)."),
        )
    fingerprint = forms.RegexField(label=_(u"PGP/GPG Fingerprint:"),
        required=False, regex=r'^[0-9]{4}/(R|D):[0-9a-fA-F]{40}$',
        widget=forms.TextInput(attrs=_attrs),
        help_text=_(u"PGP/GPG fingerprint prefixed by its size, sample:")+" 1024/D:772965E94533414EA1D4C790C793E99F8A1DE03D",
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        try:
            User.objects.get(username=cleaned_data.get('username'))
        except User.DoesNotExist:
            pass
        else:
            self._errors['username'] = ErrorList([_(u"This username is already used")])
            del cleaned_data['username']

        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            self._errors['password'] = ErrorList([_(u"The confirmation password does not match the original password")])
            del cleaned_data['password']
            del cleaned_data['password_confirm']
        return cleaned_data

class UserFormModify(UserForm):
    def __init__(self, data=None):
        super(UserFormModify, self).__init__(data)
        del self.fields['username']
        self.fields['password'].__dict__['required'] = False
        self.fields['password_confirm'].__dict__['required'] = False

    def fill_from_user(self, user):
        for field in self.__dict__['fields']:
            if user.__dict__.has_key(field):
                self.initial[field] = user.__dict__[field]
            if user.get_profile().__dict__.has_key(field):
                self.initial[field] = user.get_profile().__dict__[field]
            # foreign keys
            if user.get_profile().__dict__.has_key(field+'_id'):
                self.initial[field] = user.get_profile().__dict__[field+'_id']

class UserFormManagerCreate(UserForm):
    badge_type = forms.ModelChoiceField(label=_(u"Badge type:"),
        queryset=Badge.objects.all().order_by('-default'), widget=forms.Select(),
        empty_label=None)
    notes = forms.CharField(label=_(u"Notes:"), required=False,
        widget=forms.Textarea(attrs=_attrs))
    payment_later= forms.BooleanField(label=_(u"Payment later:"), required=False)

class UserFormManagerModify(UserFormManagerCreate, UserFormModify):
    pass