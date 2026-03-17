from rest_framework import serializers
from apps.users.serializers import PublicUserSerializer
from .models import Category, Course, Lesson, Enrollment, Review


class CategorySerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'courses_count']

    def get_courses_count(self, obj):
        return obj.courses.filter(is_published=True).count()


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Lesson
        fields = ['id', 'title', 'description', 'duration', 'order', 'is_free', 'video_url']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ro'yxatdan o'tmagan foydalanuvchi uchun video URL ni yashirish
        request = self.context.get('request')
        if not instance.is_free and (not request or not request.user.is_authenticated):
            data['video_url'] = None
        return data


class ReviewSerializer(serializers.ModelSerializer):
    student = PublicUserSerializer(read_only=True)

    class Meta:
        model  = Review
        fields = ['id', 'student', 'rating', 'comment', 'created_at']
        read_only_fields = ['student', 'created_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Reyting 1 dan 5 gacha bo\'lishi kerak')
        return value


class CourseListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun qisqa serializer"""
    category   = CategorySerializer(read_only=True)
    instructor = PublicUserSerializer(read_only=True)
    rating     = serializers.FloatField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    lessons_count  = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'slug', 'thumbnail', 'category',
            'instructor', 'price', 'is_free', 'level',
            'rating', 'students_count', 'lessons_count', 'certificate',
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    """To'liq ma'lumot"""
    category   = CategorySerializer(read_only=True)
    instructor = PublicUserSerializer(read_only=True)
    lessons    = LessonSerializer(many=True, read_only=True)
    reviews    = ReviewSerializer(many=True, read_only=True)
    rating     = serializers.FloatField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    is_enrolled    = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'slug', 'description', 'thumbnail',
            'category', 'instructor', 'price', 'is_free', 'level',
            'language', 'certificate', 'rating', 'students_count',
            'lessons', 'reviews', 'is_enrolled', 'created_at',
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user, is_active=True).exists()
        return False


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model  = Enrollment
        fields = ['id', 'course', 'enrolled_at', 'progress']
