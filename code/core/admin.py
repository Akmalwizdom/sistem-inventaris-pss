# code/core/admin.py

from django.contrib import admin
from .models import Course, CourseMember, CourseContent, Comment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'teacher')
    search_fields = ('name', 'description')

@admin.register(CourseMember)
class CourseMemberAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'course_id', 'role')
    list_filter = ('role',)

@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_id')
    search_fields = ('name',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content_id', 'member_id', 'created_at')
    search_fields = ('comment',)