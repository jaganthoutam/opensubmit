from django.contrib.auth.models import User, Group, Permission

STUDENT_TUTORS_GROUP_NAME = "Student Tutors"
COURSE_OWNERS_GROUP_NAME = "Course Owners"

def check_permission_system():
    '''
        This methods makes sure that:

        1.) All neccessary user groups exist.
        2.) All these groups have the right database permissions assigned.
        3.) Tutors have backend rights.
        4.) Course owners have backend rights.
        5.) Students have no backend rights.

        The permission objects were already generated by the Django database initialization,
        so we can assume them to be given.

        This method is idempotent and does not touch manually assigned permissions.
    '''
    tutor_perms = ( "change_submission", "delete_submission",
                    "change_submissionfile", "delete_submissionfile" )
    owner_perms = ( "add_assignment", "change_assignment", "delete_assignment",
                    "add_grading", "change_grading",  "delete_grading",
                    "add_gradingscheme", "change_gradingscheme", "delete_gradingscheme",
                    "add_submission", "change_submission", "delete_submission",
                    "add_submissionfile", "change_submissionfile", "delete_submissionfile",
                    "add_course", "change_course", "delete_course",
                    "add_studyprogram", "change_studyprogram", "delete_studyprogram",
                    "change_user", "delete_user")

    # Give all tutor users staff rights and add them to the tutors permission group
    tutors = User.objects.filter(courses_tutoring__isnull=False)
    tutors.update(is_staff=True)
    # If the app crashes here, you may have duplicate group objects, which must be fixed manually in the DB.
    tutor_group, created = Group.objects.get_or_create(name=STUDENT_TUTORS_GROUP_NAME)
    # If the app crashes here, you may have duplicate permission objects, which must be fixed manually in the DB.
    tutor_group.permissions = [Permission.objects.get(codename=perm) for perm in tutor_perms]
    tutor_group.user_set.add(*tutors)
    tutor_group.save()

    # Give all course owner users staff rights and add them to the course owners permission group
    owners = User.objects.filter(courses__isnull=False)
    owners.update(is_staff=True)
    # If the app crashes here, you may have duplicate group objects, which must be fixed manually in the DB.
    owner_group, created = Group.objects.get_or_create(name=COURSE_OWNERS_GROUP_NAME)
    # If the app crashes here, you may have duplicate permission objects, which must be fixed manually in the DB.
    owner_group.permissions = [Permission.objects.get(codename=perm) for perm in owner_perms]
    owner_group.user_set.add(*owners)
    owner_group.save()

    # Make sure that pure students (no tutor, no course owner, no superuser) have no backend access at all
    pure_students = User.objects.filter(courses__isnull=True, courses_tutoring__isnull=True, is_superuser=False)
    pure_students.update(is_staff=False)

def _get_user_groups():
    owner_group, created = Group.objects.get_or_create(name=COURSE_OWNERS_GROUP_NAME)
    if created:
        check_permission_system()
    tutor_group, created = Group.objects.get_or_create(name=STUDENT_TUTORS_GROUP_NAME)
    if created:
        check_permission_system()
    return tutor_group, owner_group

def make_student(user):
    '''
    Makes the given user a student.
    '''
    tutor_group, owner_group = _get_user_groups()
    user.is_staff=False
    user.is_superuser=False
    user.save()
    owner_group.user_set.remove(user)
    owner_group.save()
    tutor_group.user_set.remove(user)
    tutor_group.save()

def make_tutor(user):
    '''
    Makes the given user a tutor.
    '''
    tutor_group, owner_group = _get_user_groups()
    user.is_staff=True
    user.is_superuser=False
    user.save()
    owner_group.user_set.remove(user)
    owner_group.save()
    tutor_group.user_set.add(user)
    tutor_group.save()

def make_owner(user):
    '''
    Makes the given user a owner.
    '''
    tutor_group, owner_group = _get_user_groups()
    user.is_staff=True
    user.is_superuser=False
    user.save()
    owner_group.user_set.add(user)
    owner_group.save()
    tutor_group.user_set.add(user)
    tutor_group.save()

def make_admin(user):
    '''
    Makes the given user an admin.
    '''
    tutor_group, owner_group = _get_user_groups()
    user.is_staff=True
    user.is_superuser=True
    user.save()
    owner_group.user_set.add(user)
    owner_group.save()
    tutor_group.user_set.add(user)
    tutor_group.save()
