from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from account.models import UserProfile


# Define an inline admin descriptor for UserProfile model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = 'user'
    max_num = 1

# Define a new UserAdmin class
class MyUserAdmin(UserAdmin):
    inlines = [UserProfileInline, ]

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
