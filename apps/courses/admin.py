from django.contrib import admin
from .models import Category, Course, Lesson, Enrollment, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


class LessonInline(admin.TabularInline):
    model  = Lesson
    extra  = 1
    fields = ['title', 'order', 'duration', 'is_free', 'video_url']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ['title', 'instructor', 'category', 'price', 'is_free', 'is_published', 'created_at']
    list_filter   = ['is_published', 'is_free', 'level', 'category']
    search_fields = ['title', 'instructor__full_name']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published']
    inlines       = [LessonInline]

    fieldsets = (
        ('Asosiy',     {'fields': ('title', 'slug', 'description', 'thumbnail')}),
        ('Kategoriya', {'fields': ('category', 'instructor', 'level', 'language')}),
        ('Narx',       {'fields': ('price', 'is_free')}),
        ('Holat',      {'fields': ('is_published', 'certificate')}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = ['student', 'course', 'enrolled_at', 'progress', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['student__full_name', 'course__title']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['student', 'course', 'rating', 'created_at']
    list_filter   = ['rating']
