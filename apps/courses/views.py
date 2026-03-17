from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Category, Course, Enrollment, Review
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    EnrollmentSerializer, ReviewSerializer,
)


class IsInstructorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('instructor', 'admin')


# ── Kategoriyalar ────────────────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    """GET /api/v1/courses/categories/"""
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    permission_classes = [permissions.AllowAny]


# ── Kurslar ──────────────────────────────────────────────────────────────────

class CourseListView(generics.ListAPIView):
    """GET /api/v1/courses/ — Barcha nashr etilgan kurslar, filtr va qidiruv"""
    serializer_class   = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['title', 'description', 'instructor__full_name']
    ordering_fields    = ['price', 'created_at']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = Course.objects.filter(is_published=True).select_related('category', 'instructor')
        category = self.request.query_params.get('category')
        level    = self.request.query_params.get('level')
        is_free  = self.request.query_params.get('is_free')
        if category:
            qs = qs.filter(category__slug=category)
        if level:
            qs = qs.filter(level=level)
        if is_free == 'true':
            qs = qs.filter(is_free=True)
        return qs


class CourseDetailView(generics.RetrieveAPIView):
    """GET /api/v1/courses/<slug>/"""
    queryset           = Course.objects.filter(is_published=True)
    serializer_class   = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = 'slug'


class InstructorCourseCreateView(generics.CreateAPIView):
    """POST /api/v1/courses/create/ — Ustoz kurs yaratadi"""
    serializer_class   = CourseDetailSerializer
    permission_classes = [IsInstructorOrAdmin]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)


class InstructorCourseUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/courses/<slug>/manage/"""
    serializer_class   = CourseDetailSerializer
    permission_classes = [IsInstructorOrAdmin]
    lookup_field       = 'slug'

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Course.objects.all()
        return Course.objects.filter(instructor=self.request.user)


# ── Yozilish ─────────────────────────────────────────────────────────────────

class EnrollView(APIView):
    """POST /api/v1/courses/<slug>/enroll/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)

        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({'error': 'Siz allaqachon yozilgansiz'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Pullik kurs uchun to'lov tekshiruvi
        if not course.is_free:
            from apps.payments.models import Payment
            paid = Payment.objects.filter(
                user=request.user, course=course, status='completed'
            ).exists()
            if not paid:
                return Response(
                    {'error': 'Kurs uchun to\'lov qilinmagan', 'requires_payment': True},
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

        enrollment = Enrollment.objects.create(student=request.user, course=course)
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


class MyCoursesView(generics.ListAPIView):
    """GET /api/v1/courses/my/ — O'quvchining kurslari"""
    serializer_class   = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user, is_active=True
        ).select_related('course')


# ── Sharhlar ─────────────────────────────────────────────────────────────────

class ReviewCreateView(generics.CreateAPIView):
    """POST /api/v1/courses/<slug>/review/"""
    serializer_class   = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        serializer.save(student=self.request.user, course=course)
