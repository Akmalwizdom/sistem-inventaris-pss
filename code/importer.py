import os
import sys
import csv
import json
from random import randint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplelms.settings')

import django
django.setup()

from django.contrib.auth.models import User
from core.models import Course, CourseMember, CourseContent, Comment

# 1) Import Users dari CSV
with open(os.path.join(BASE_DIR, 'csv_data', 'user-data.csv'), newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for num, row in enumerate(reader):
        if not User.objects.filter(username=row['username']).exists():
            User.objects.create_user(
                id=num + 2,
                username=row['username'],
                email=row.get('email', ''),
                password=row['password'],
            )

# 2) Import Courses dari CSV
with open(os.path.join(BASE_DIR, 'csv_data', 'course-data.csv'), newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for num, row in enumerate(reader):
        if not Course.objects.filter(pk=num + 1).exists():
            Course.objects.create(
                id=num + 1,
                name=row['name'],
                description=row['description'],
                price=int(row['price']),
                teacher=User.objects.get(pk=int(row['teacher']))
            )

# 3) Import CourseMember dari CSV
with open(os.path.join(BASE_DIR, 'csv_data', 'member-data.csv'), newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for num, row in enumerate(reader):
        if not CourseMember.objects.filter(pk=num + 1).exists():
            CourseMember.objects.create(
                id=num + 1,
                course_id=Course.objects.get(pk=int(row['course_id'])),
                user_id=User.objects.get(pk=int(row['user_id'])),
                role=row['role'],
            )

# 4) Import CourseContent dari JSON
contents_file = os.path.join(BASE_DIR, 'csv_data', 'contents.json')
if os.path.exists(contents_file):
    with open(contents_file, 'r', encoding='utf-8') as jsonfile:
        contents = json.load(jsonfile)
        obj_create = []
        for num, row in enumerate(contents):
            if not CourseContent.objects.filter(pk=num+1).exists():
                obj_create.append(
                    CourseContent(
                        course_id=Course.objects.get(pk=int(row['course_id'])),
                        video_url=row['video_url'],
                        name=row['name'],
                        description=row['description'],
                        id=num+1
                    )
                )
        if obj_create:
            CourseContent.objects.bulk_create(obj_create, ignore_conflicts=True)

# 5) Import Comment dari JSON
comments_file = os.path.join(BASE_DIR, 'csv_data', 'comments.json')
if os.path.exists(comments_file):
    with open(comments_file, 'r', encoding='utf-8') as jsonfile:
        comments = json.load(jsonfile)
        obj_create = []
        for num, row in enumerate(comments):
            user_id = int(row['user_id'])
            if user_id > 50:
                user_id = randint(5, 40)
            
            if not Comment.objects.filter(pk=num+1).exists():
                obj_create.append(
                    Comment(
                        content_id=CourseContent.objects.get(pk=int(row['content_id'])),
                        member_id=CourseMember.objects.get(user_id=user_id, course_id__content__id=int(row['content_id'])),
                        comment=row['comment'],
                        id=num+1
                    )
                )
        if obj_create:
            Comment.objects.bulk_create(obj_create, ignore_conflicts=True)

print('Import selesai ✅')