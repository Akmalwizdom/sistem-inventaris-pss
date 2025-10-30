from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Avg, Count, Max, Min, Sum
from django.http import JsonResponse
import json

from core.models import Course, CourseContent, CourseMember, Comment
from django.shortcuts import render 


# ------------------------------------------------------
# Fungsi bantu / demo
# ------------------------------------------------------
def create_test_user(request):
    user = User.objects.create_user(
        username="usertesting",
        email="usertest@email1.com",
        password="sandietesting",
    )
    return JsonResponse({"id": user.id, "username": user.username})


def create_course_from_query(request):
    row = {
        "name": request.GET.get("name", "Nama Default"),
        "description": request.GET.get("description", "-"),
        "price": int(request.GET.get("price", 10000)),
    }
    teacher = User.objects.get(pk=1)
    course = Course.objects.create(
        name=row["name"],
        description=row["description"],
        price=row["price"],
        teacher=teacher,
    )
    return JsonResponse({"id": course.id, "name": course.name})


# ------------------------------------------------------
# Fungsi Read (Select)
# ------------------------------------------------------
def select_all_users(request):
    users = User.objects.all()
    user_list = [
        {"id": user.id, "username": user.username, "email": user.email}
        for user in users
    ]
    return JsonResponse({"users": user_list})


def select_single_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
        data = {"id": user.id, "username": user.username, "email": user.email}
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


# ------------------------------------------------------
# Fungsi Update & Delete
# ------------------------------------------------------
def update_user_data(request, pk):
    try:
        user = User.objects.get(pk=pk)
        new_username = request.POST.get("username", user.username)
        user.username = new_username
        user.save()
        return JsonResponse({"status": "success", "username_baru": user.username})
    except User.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "User tidak ditemukan"}, status=404
        )


def delete_user_data(request, pk):
    try:
        user = User.objects.get(pk=pk)
        user.delete()
        return JsonResponse({"status": "success", "message": f"User ID {pk} telah dihapus"})
    except User.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "User tidak ditemukan"}, status=404
        )
    
def delete_all_user_data(request, exclude_user_id):
    try:
        # Hapus semua pengguna kecuali user dengan ID tertentu
        User.objects.exclude(id=exclude_user_id).delete()
        return JsonResponse({"status": "success", "message": f"Semua pengguna kecuali ID {exclude_user_id} telah dihapus"})
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"Pengguna dengan ID {exclude_user_id} tidak ditemukan"}, status=404)


def delete_all_course_data(request):
    Course.objects.all().delete()
    return JsonResponse({"status": "success", "message": "Semua data kursus telah dihapus"})


# ------------------------------------------------------
# Fungsi Statistik & Seleksi Kursus
# ------------------------------------------------------
def courseStat(request):
    courses = Course.objects.all()
    course_with_member_count = Course.objects.annotate(
        member_count=Count('coursemember')
    )

    stats = courses.aggregate(
        max_price=Max('price'),
        min_price=Min('price'),
        avg_price=Avg('price')
    )

    cheapest = Course.objects.filter(price=stats['min_price']).first()
    expensive = Course.objects.filter(price=stats['max_price']).first()

    popular = course_with_member_count.order_by('-member_count')[:5]
    unpopular = course_with_member_count.order_by('member_count')[:5]

    def serialize_course(course_queryset):
        data = []
        for course in course_queryset:
            member_count = getattr(course, 'member_count', 0)
            data.append({
                'id': course.id,
                'name': course.name,
                'price': course.price,
                'member_count': member_count
            })
        return data

    result = {
        'course_count': len(courses),
        'price_stats': {
            'average': stats['avg_price'],
            'highest': stats['max_price'],
            'lowest': stats['min_price']
        },
        'cheapest': {
            'id': cheapest.id if cheapest else None,
            'name': cheapest.name if cheapest else None,
            'price': cheapest.price if cheapest else None
        } if cheapest else None,
        'expensive': {
            'id': expensive.id if expensive else None,
            'name': expensive.name if expensive else None,
            'price': expensive.price if expensive else None
        } if expensive else None,
        'popular': serialize_course(popular),
        'unpopular': serialize_course(unpopular),
    }
    return JsonResponse(result, safe=False)


def allUserStat(request):
    users = User.objects.all()
    user_stats = User.objects.annotate(
        courses_created=Count('course', distinct=True),
        courses_followed_count=Count('coursemember', distinct=True)
    )

    user_creator_count = user_stats.filter(courses_created__gt=0).count()
    user_no_course_created_count = user_stats.filter(courses_created=0).count()
    avg_followed = user_stats.aggregate(
        avg_followed=Avg('courses_followed_count')
    )['avg_followed']

    most_followed_user = user_stats.order_by('-courses_followed_count').first()
    no_followed_courses = user_stats.filter(courses_followed_count=0).values('username', 'email')

    result = {
        'non_admin_count': users.count(), 
        'user_creator_count': user_creator_count,
        'user_no_course_created_count': user_no_course_created_count,
        'average_followed_courses': avg_followed if avg_followed else 0,
        'most_followed_user': {
            'id': most_followed_user.id,
            'username': most_followed_user.username,
            'followed_count': most_followed_user.courses_followed_count
        } if most_followed_user else None,
        'users_not_following_any': list(no_followed_courses)
    }
    return JsonResponse(result, safe=False)

# Di core/views.py

def userDetailStat(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        user_agg = User.objects.annotate(
            followed_count=Count('coursemember', distinct=True),
            created_count=Count('course', distinct=True),
            total_comments=Count('coursemember__comment', distinct=True) 
        ).get(pk=user_id)

        followed_count = user_agg.followed_count
        created_count = user_agg.created_count
        total_members_in_created_courses = Course.objects.filter(
            teacher=user
        ).annotate(
            member_count=Count('coursemember', distinct=True)
        ).aggregate(
            total_members=Sum('member_count')
        )['total_members'] or 0

        comment_count = user_agg.total_comments

        result = {
            'user_details': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'followed_course_count': followed_count,
            'created_course_count': created_count,
            'total_members_in_created_courses': total_members_in_created_courses,
            'posted_comment_count': comment_count,
        }
        return JsonResponse(result, safe=False)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
# Di core/views.py

def courseDetailStat(request, course_id):
    try:
        course_data = Course.objects.annotate(
            member_count=Count('coursemember', distinct=True),
            content_count=Count('coursecontent', distinct=True),
        ).annotate(
            comment_count=Count('coursecontent__comment', distinct=True)
        ).get(pk=course_id)

        contents = CourseContent.objects.filter(course_id=course_data.id).annotate(
            comment_count_content=Count('comment', distinct=True)
        ).order_by('-comment_count_content')[:3]

        most_commented_contents = []
        for content in contents:
            most_commented_contents.append({
                'name': content.name,
                'comment_count': content.comment_count_content
            })

        result = {
            'name': course_data.name,
            'description': course_data.description,
            'price': course_data.price,
            'member_count': course_data.member_count,
            'content_count': course_data.content_count,
            'total_comment_count': course_data.comment_count,
            'teacher': {
                'username': course_data.teacher.username,
                'email': course_data.teacher.email,
                'full_name': f"{course_data.teacher.first_name} {course_data.teacher.last_name}",
            },
            'most_commented_content': most_commented_contents
        }
        return JsonResponse(result, safe=False)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)    

def courseMemberStat(request):
    courses = Course.objects.filter(description__contains='python') \
        .annotate(member_num=Count('coursemember'))

    course_data = []
    for course in courses:
        record = {
            'id': course.id,
            'name': course.name,
            'price': course.price,
            'member_count': course.member_num
        }
        course_data.append(record)

    result = {
        'data_count': len(course_data),
        'data': course_data
    }
    return JsonResponse(result)


def allCourse(request):
    all_course = Course.objects.all()
    result = []

    for course in all_course:
        record = {
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'price': course.price,
            'teacher': {
                'id': course.teacher.id,
                'username': course.teacher.username,
                'email': course.teacher.email,
                'fullname': f"{course.teacher.first_name} {course.teacher.last_name}"
            }
        }
        result.append(record)

    return JsonResponse(result, safe=False)


def userCourses(request):
    user = User.objects.get(pk=3)
    courses = Course.objects.filter(teacher=user.id)

    course_data = []
    for course in courses:
        record = {
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'price': course.price
        }
        course_data.append(record)

    result = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'fullname': f"{user.first_name} {user.last_name}",
        'courses': course_data
    }
    return JsonResponse(result, safe=False)


# ------------------------------------------------------
# Fungsi Testing / Validasi
# ------------------------------------------------------
def testing(request):
    user_test = User.objects.filter(username="usertesting")
    if not user_test.exists():
        user_test = User.objects.create_user(
            username="usertesting",
            email="usertest@email.com",
            password="sanditesting"
        )
    all_users = serializers.serialize('python', User.objects.all())
    admin = User.objects.get(pk=1)
    user_test.delete()
    after_delete = serializers.serialize('python', User.objects.all())
    response = {
        "admin_user": serializers.serialize('python', [admin])[0],
        "all_users": all_users,
        "after_del": after_delete,
    }
    return JsonResponse(response)