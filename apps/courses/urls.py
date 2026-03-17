from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.CourseListView.as_view(),           name='course_list'),
    path('categories/',               views.CategoryListView.as_view(),         name='category_list'),
    path('create/',                   views.InstructorCourseCreateView.as_view(), name='course_create'),
    path('my/',                       views.MyCoursesView.as_view(),            name='my_courses'),
    path('<slug:slug>/',              views.CourseDetailView.as_view(),         name='course_detail'),
    path('<slug:slug>/enroll/',       views.EnrollView.as_view(),               name='enroll'),
    path('<slug:slug>/review/',       views.ReviewCreateView.as_view(),         name='review_create'),
    path('<slug:slug>/manage/',       views.InstructorCourseUpdateView.as_view(), name='course_manage'),
]
