from django.urls import path
from . import views # Impor modul views saja

urlpatterns = [
    path("create-test-user/", views.create_test_user, name="create_test_user"),
    path("create-course/", views.create_course_from_query, name="create_course"),

    # URL untuk Operasi SELECT/READ
    path("users/", views.select_all_users, name="select_all_users"),
    path("users/<int:pk>/", views.select_single_user, name="select_single_user"),

    # URL untuk Operasi UPDATE/DELETE
    path("users/<int:pk>/update/", views.update_user_data, name="update_user"),
    path("users/<int:pk>/delete/", views.delete_user_data, name="delete_user"),
    path("courses/delete-all/", views.delete_all_course_data, name="delete_all_courses"),
    path("users/delete-all/<int:exclude_user_id>/", views.delete_all_user_data, name="delete_all_users"),

    path('testing/', views.testing, name='testing'),

    path('stats/courses/', views.courseStat, name='course-stat'),
    path('stats/course-members/', views.courseMemberStat, name='course-member-stat'),
    path('courses/all/', views.allCourse, name='all-course'),
    path('courses/by-user/', views.userCourses, name='user-courses'),

    path('stats/users/', views.allUserStat, name='all-user-stat'),
    path('stats/user/<int:user_id>/', views.userDetailStat, name='user-detail-stat'),
    path('stats/course/<int:course_id>/', views.courseDetailStat, name='course-detail-stat'),
    
]