from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, default='📚')

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Kategoriyalar'

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner',     'Boshlang\'ich'),
        ('intermediate', 'O\'rta'),
        ('advanced',     'Yuqori'),
    ]

    title       = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    description = models.TextField()
    thumbnail   = models.ImageField(upload_to='courses/thumbnails/')
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    instructor  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    price       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    level       = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    language    = models.CharField(max_length=50, default='O\'zbek')
    is_free     = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    certificate = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def students_count(self):
        return self.enrollments.filter(is_active=True).count()

    @property
    def lessons_count(self):
        return self.lessons.count()


class Lesson(models.Model):
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url   = models.URLField(blank=True)
    duration    = models.PositiveIntegerField(default=0, help_text='Daqiqada')
    order       = models.PositiveIntegerField(default=0)
    is_free     = models.BooleanField(default=False)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Enrollment(models.Model):
    """O'quvchining kursg yozilishi"""
    student    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active   = models.BooleanField(default=True)
    progress    = models.PositiveSmallIntegerField(default=0)  # 0-100%

    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'course']

    def __str__(self):
        return f'{self.student.full_name} → {self.course.title}'


class Review(models.Model):
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating     = models.PositiveSmallIntegerField()   # 1–5
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ['course', 'student']

    def __str__(self):
        return f'{self.student.full_name} — {self.course.title} ({self.rating}★)'
