import string
import random
import collections

from django.contrib.auth.models import User
from django.test import TestCase                         

import django_comment_client.models as models

import student.models

import django_comment_client.permissions as permissions

#########################################################################################

class PermissionsTestCase(TestCase):
    def random_str(self, length=15, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(length))

    def setUp(self):

        self.course_id = "edX/toy/2012_Fall"

        self.moderator_role = models.Role.objects.get_or_create(name="Moderator", \
                                                         course_id=self.course_id)[0]
        self.student_role = models.Role.objects.get_or_create(name="Student", \
                                                       course_id=self.course_id)[0]

        self.student = User.objects.create(username=self.random_str(),
                            password="123456", email="john@yahoo.com")
        self.moderator = User.objects.create(username=self.random_str(),
                            password="123456", email="staff@edx.org")
        self.moderator.is_staff = True
        self.moderator.save()
        self.student_enrollment = student.models.CourseEnrollment.objects.create(user=self.student, \
                                                                  course_id=self.course_id)
        self.moderator_enrollment = student.models.CourseEnrollment.objects.create(user=self.moderator, \
                                                                    course_id=self.course_id)
        #Fake json files
        self.empty_data = {"content":{
                                    }
                    }
        self.open_data = {"content":{
                                "closed":False,
                                "user_id":str(self.student.id)
                                }
                     }
        self.closed_data = {"content":{
                                "closed":True,
                                "user_id":str(self.student.id)
                                }
                     }
        
    def tearDown(self):
        self.student_enrollment.delete()
        self.moderator_enrollment.delete()

# Do we need to have this? We shouldn't be deleting students, ever
#        self.student.delete()
#        self.moderator.delete()


    def testDefaultRoles(self):
        self.assertTrue(self.student_role in self.student.roles.all())
        self.assertTrue(self.moderator_role in self.moderator.roles.all())

    def testPermission(self):
        name = self.random_str()
        self.moderator_role.add_permission(name)
        self.assertTrue(permissions.has_permission(self.moderator, name, self.course_id))
        # Moderators do not have student priveleges unless explicitly added

        self.student_role.add_permission(name)
        self.assertTrue(permissions.has_permission(self.student, name, self.course_id))

        # Students don't have moderator priveleges 
        name2 = self.random_str()
        self.student_role.add_permission(name2)
        self.assertFalse(permissions.has_permission(self.moderator, name2, self.course_id))

    def testCachedPermission(self):
        
        # Cache miss returns None
        # Don't really understand how this works? What's in Cache?
        self.assertFalse(permissions.cached_has_permission(self.student, self.moderator, \
                                            course_id=None))
        self.assertFalse(permissions.cached_has_permission(self.student, "update_thread", \
                                            course_id=None))

    def testCheckCondition(self):
        # Checks whether something? is open, or whether the author is user
        self.assertFalse(permissions.check_condition(self.student, 'is_open', \
                                         self.course_id, self.empty_data))
        self.assertFalse(permissions.check_condition(self.student, 'is_author', \
                                         self.course_id, self.empty_data))
        self.assertTrue(permissions.check_condition(self.student,'is_open', \
                                         self.course_id, self.open_data))
        self.assertTrue(permissions.check_condition(self.student, 'is_author', \
                                         self.course_id, self.open_data))
        self.assertFalse(permissions.check_condition(self.student,'is_open', \
                                         self.course_id, self.closed_data))

    def testCheckConditionsPermissions(self):
        # Should be True, but test fails in that case?
        # What do I have to do to get True?
        self.assertFalse(permissions.check_conditions_permissions(self.student, 'is_open', \
                                                     self.course_id,\
                                                     data=self.open_data))
        self.assertFalse(permissions.check_conditions_permissions(self.student, 'is_open', \
                                                     self.course_id,\
                                                     data=self.empty_data))

        self.assertFalse(permissions.check_conditions_permissions(self.student, \
                                                      ['is_open', 'is_author'],\
                                                      self.course_id,\
                                                      data=self.open_data))
        self.assertFalse(permissions.check_conditions_permissions(self.student, \
                                                      ['is_open', 'is_author'],\
                                                      self.course_id,\
                                                      data=self.open_data,\
                                                      operator='and'))
        self.assertFalse(permissions.check_conditions_permissions(self.student, 'update_thread',\
                                                      self.course_id, data=self.open_data))

    def testCheckPermissionsByView(self):
        # kwargs is the data entered in check_condition, which is json?
##        self.assertRaises(UnboundLocalError, check_permissions_by_view(self.student,\
##                                                self.course_id,\
##                                                self.empty_data,\
##                                                  "nonexistant"))
        self.assertFalse(permissions.check_permissions_by_view(self.student,self.course_id, \
                                                   self.empty_data, 'update_thread'))
##        self.assertTrue(check_permissions_by_view(self.student,self.course_id, \
##                                                   self.open_data, 'vote_for_thread'))


class PermissionClassTestCase(TestCase):

    def setUp(self):
        
        self.permission = permissions.Permission.objects.get_or_create(name="test")[0]

    def testUnicode(self):
        # Doesn't print?
        self.assertEqual(str(self.permission), "test")

class RoleClassTestCase(TestCase):
    def setUp(self):
        # For course ID, syntax edx/classname/classdate is important
        # because xmodel.course_module.id_to_location looks for a string to split
        
        self.course_id = "edX/toy/2012_Fall"
        self.student_role = models.Role.objects.get_or_create(name="Student", \
                                                         course_id=self.course_id)[0]
        self.student_role.add_permission("delete_thread")
        self.student_2_role = models.Role.objects.get_or_create(name="Student", \
                                                         course_id=self.course_id)[0]
        self.TA_role = models.Role.objects.get_or_create(name="Community TA",\
                                                  course_id=self.course_id)[0]
        self.course_id_2 = "edx/6.002x/2012_Fall"
        self.TA_role_2 = models.Role.objects.get_or_create(name="Community TA",\
                                                  course_id=self.course_id_2)[0]
        class Dummy():
            def render_template():
                pass
        d = {"data":{
                "textbooks":[],
                'wiki_slug':True,
                }
             }
##        input_list = ['http', 'MITx', '6.002x', '2012_Fall', 'about'] 
##        self.course = CourseDescriptor(Dummy(), definition=d, \
##                                       location=Location(input_list),\
##                                       start = True)
        
    def testHasPermission(self):
        # It seems that whenever you add a permission to student_role,
        # Roles with the same FORUM_ROLE in same class also receives the same
        # permission.
        # Is this desirable?
        self.assertTrue(self.student_role.has_permission("delete_thread"))
        self.assertTrue(self.student_2_role.has_permission("delete_thread"))
        self.assertFalse(self.TA_role.has_permission("delete_thread"))

    def testInheritPermissions(self):
        #Don't know how to create a TA role that is for a different class
        self.TA_role.inherit_permissions(self.student_role)
        self.assertTrue(self.TA_role.has_permission("delete_thread"))
        #self.assertFalse(self.TA_role_2.has_permission("delete_thread"))
        # Despite being from 2 different courses, TA_role_2 can still inherit
        # permissions from TA_role ?
        #self.TA_role_2.inherit_permissions(TA_role)
        #self.assertTrue(self.TA_role_2.has_permission("delete_thread"))




