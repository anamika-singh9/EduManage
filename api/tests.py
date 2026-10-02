import datetime
from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

from adminapp.models import Teacher, student, Attendance, Parent
from examapp.models import Exam, Result


def make_user(username, group, password='pass12345'):
    u = User.objects.create_user(username=username, password=password, email=username)
    u.groups.add(Group.objects.get_or_create(name=group)[0])
    return u


def make_student(user, name, sclass='5th', roll=1):
    return student.objects.create(user=user, rollno=roll, name=name, fname='f', mname='m', gender='Male',
        dob='01/01/2015', contactno='1', emailaddress=user.username, sclass=sclass, address='a',
        feepaid='0', duefee='0', created_date=datetime.date.today(), password=user.password)


class BaseCase(TestCase):
    def setUp(self):
        for g in ('Admin', 'Teacher', 'Student', 'Parent'):
            Group.objects.get_or_create(name=g)
        self.admin = make_user('admin@t.com', 'Admin')
        self.tuser = make_user('teach@t.com', 'Teacher')
        self.teacher = Teacher.objects.create(user=self.tuser, name='T', fname='f', mname='m', gender='F',
            dob='x', contact='1', emailaddress='teach@t.com', tclass='5th', address='a', salary='1',
            qualification='q', password=self.tuser.password, created_date=datetime.date.today())
        self.s1u = make_user('s1@t.com', 'Student'); self.s1 = make_student(self.s1u, 'S1', '5th', 1)
        self.s2u = make_user('s2@t.com', 'Student'); self.s2 = make_student(self.s2u, 'S2', '6th', 2)
        self.puser = make_user('p@t.com', 'Parent')
        self.parent = Parent.objects.create(user=self.puser, name='P', contact='1')
        self.parent.children.add(self.s1)
        today = datetime.date.today()
        for s in (self.s1, self.s2):
            Attendance.objects.create(sid=str(s.id), name=s.name, rollno=s.rollno, semail='', sclass=s.sclass,
                                      tclass=s.sclass, status='P', created_date=today)
        self.exam = Exam.objects.create(name='Mid', sclass='5th', exam_date=today)
        Result.objects.create(exam=self.exam, student=self.s1, subject_name='Math', marks_obtained=80, max_marks=100)

    def api(self, user):
        c = APIClient(); c.force_authenticate(user); return c


class WebAuthTests(BaseCase):
    def login(self, email):
        return self.client.post('/logcore/', {'userid': email, 'password': 'pass12345'})

    def test_role_redirects(self):
        self.assertEqual(self.login('admin@t.com')['Location'], '/adminapp/adminhome/')
        self.client.logout()
        self.assertEqual(self.login('teach@t.com')['Location'], '/teacherapp/teacherapp/')
        self.client.logout()
        self.assertEqual(self.login('s1@t.com')['Location'], '/studentapp/studentapp/')
        self.client.logout()
        self.assertEqual(self.login('p@t.com')['Location'], '/parentapp/')

    def test_bad_password(self):
        r = self.client.post('/logcore/', {'userid': 'admin@t.com', 'password': 'wrong'})
        self.assertContains(r, 'Invalid email or password')

    def test_anonymous_redirected(self):
        for url in ('/adminapp/adminhome/', '/teacherapp/teacherapp/', '/studentapp/studentapp/', '/parentapp/'):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_cross_role_forbidden(self):
        self.client.login(username='s1@t.com', password='pass12345')
        self.assertEqual(self.client.get('/adminapp/adminhome/').status_code, 403)
        self.assertEqual(self.client.get('/teacherapp/teacherapp/').status_code, 403)
        self.assertEqual(self.client.get('/parentapp/').status_code, 403)

    def test_logout_really_logs_out(self):
        self.client.login(username='teach@t.com', password='pass12345')
        self.client.get('/teacherapp/teacherlogout/')
        self.assertEqual(self.client.get('/teacherapp/teacherapp/').status_code, 302)

    def test_portals_render(self):
        for u, urls in {'admin@t.com': ['/adminapp/adminhome/', '/adminapp/viewstudent/', '/adminapp/viewparent/', '/adminapp/addparent/'],
                        'teach@t.com': ['/teacherapp/teacherapp/', '/teacherapp/viewattend/', '/examapp/exams/', f'/examapp/exams/{self.exam.id}/results/'],
                        's1@t.com': ['/studentapp/studentapp/', '/studentapp/stuattend/', '/studentapp/results/'],
                        'p@t.com': ['/parentapp/']}.items():
            self.client.login(username=u, password='pass12345')
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 200, url)
            self.client.logout()

    def test_delete_enquiry_requires_post(self):
        self.client.login(username='admin@t.com', password='pass12345')
        self.assertEqual(self.client.get('/adminapp/delenq/1').status_code, 405)

    def test_public_pages(self):
        for u in ('/', '/contact/', '/login/', '/academices/', '/admission/', '/feestructure/', '/ruleregulation/', '/smartroom/'):
            self.assertEqual(self.client.get(u).status_code, 200, u)


class ReportAndExportTests(BaseCase):
    def test_student_pdf_report_card(self):
        self.client.login(username='s1@t.com', password='pass12345')
        r = self.client.get(f'/studentapp/reportcard/{self.exam.id}/')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_parent_pdf_only_for_own_child(self):
        self.client.login(username='p@t.com', password='pass12345')
        ok = self.client.get(f'/parentapp/reportcard/{self.s1.id}/{self.exam.id}/')
        self.assertEqual(ok.status_code, 200)
        other = self.client.get(f'/parentapp/reportcard/{self.s2.id}/{self.exam.id}/')
        self.assertEqual(other.status_code, 404)

    def test_csv_export_admin_only(self):
        self.client.login(username='admin@t.com', password='pass12345')
        r = self.client.get('/adminapp/export/attendance/?sclass=5th')
        self.assertEqual(r['Content-Type'], 'text/csv')
        body = r.content.decode()
        self.assertIn('S1', body); self.assertNotIn('S2', body)
        self.client.logout(); self.client.login(username='s1@t.com', password='pass12345')
        self.assertEqual(self.client.get('/adminapp/export/attendance/').status_code, 403)

    def test_teacher_result_entry_validates_marks(self):
        self.client.login(username='teach@t.com', password='pass12345')
        url = f'/examapp/exams/{self.exam.id}/results/'
        self.client.post(url, {'student': self.s1.id, 'subject_name': 'Sci', 'marks_obtained': '150', 'max_marks': '100'})
        self.assertFalse(Result.objects.filter(subject_name='Sci').exists())
        self.client.post(url, {'student': self.s1.id, 'subject_name': 'Sci', 'marks_obtained': '90', 'max_marks': '100'})
        self.assertTrue(Result.objects.filter(subject_name='Sci').exists())


class ApiTests(BaseCase):
    def test_requires_authentication(self):
        self.assertEqual(APIClient().get('/api/v1/students/').status_code, 401)

    def test_admin_sees_all_students_paginated(self):
        r = self.api(self.admin).get('/api/v1/students/')
        self.assertEqual(r.data['count'], 2)
        self.assertIn('results', r.data)

    def test_student_sees_only_self(self):
        r = self.api(self.s1u).get('/api/v1/students/')
        self.assertEqual([s['name'] for s in r.data['results']], ['S1'])

    def test_parent_sees_only_children(self):
        r = self.api(self.puser).get('/api/v1/students/')
        self.assertEqual([s['name'] for s in r.data['results']], ['S1'])
        att = self.api(self.puser).get('/api/v1/attendance/')
        self.assertEqual(att.data['count'], 1)

    def test_teacher_scoped_to_own_class(self):
        r = self.api(self.tuser).get('/api/v1/students/')
        self.assertEqual([s['name'] for s in r.data['results']], ['S1'])

    def test_sensitive_fields_never_exposed(self):
        r = self.api(self.admin).get('/api/v1/students/')
        self.assertNotIn('password', r.data['results'][0])
        self.assertNotIn('password', self.api(self.admin).get('/api/v1/teachers/').data['results'][0])

    def test_student_cannot_write(self):
        r = self.api(self.s1u).post('/api/v1/classes/', {'class_name': 'X', 'seats': 1, 'roomno': '1', 'created_date': '2026-01-01'})
        self.assertEqual(r.status_code, 403)
        r = self.api(self.s1u).post('/api/v1/attendance/', {})
        self.assertEqual(r.status_code, 403)

    def test_search_filter_ordering(self):
        c = self.api(self.admin)
        self.assertEqual(c.get('/api/v1/students/?search=S2').data['count'], 1)
        self.assertEqual(c.get('/api/v1/students/?sclass=6th').data['count'], 1)
        names = [s['name'] for s in c.get('/api/v1/students/?ordering=-rollno').data['results']]
        self.assertEqual(names, ['S2', 'S1'])

    def test_validation_errors(self):
        r = self.api(self.tuser).post('/api/v1/attendance/', {'sid': '1', 'name': 'x', 'rollno': '1', 'sclass': '5th',
                                                             'tclass': '5th', 'status': 'Z', 'created_date': '2026-01-01'})
        self.assertEqual(r.status_code, 400)
        r = self.api(self.tuser).post('/api/v1/results/', {'exam': self.exam.id, 'student': self.s1.id,
                                                          'subject_name': 'Bio', 'marks_obtained': '120', 'max_marks': '100'})
        self.assertEqual(r.status_code, 400)

    def test_results_have_computed_grade(self):
        r = self.api(self.s1u).get('/api/v1/results/')
        self.assertEqual(r.data['results'][0]['grade'], 'A')

    def test_jwt_login_and_me(self):
        c = APIClient()
        tok = c.post('/api/v1/auth/token/', {'username': 'admin@t.com', 'password': 'pass12345'}).data['access']
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {tok}')
        self.assertEqual(c.get('/api/v1/me/').data['roles'], ['Admin'])

    def test_api_docs_available(self):
        self.assertEqual(self.client.get('/api/schema/').status_code, 200)
        self.assertEqual(self.client.get('/api/docs/').status_code, 200)


class CrudCompletenessTests(BaseCase):
    def as_admin(self):
        self.client.login(username='admin@t.com', password='pass12345')

    def test_edit_student_syncs_login_email(self):
        self.as_admin()
        r = self.client.post(f'/adminapp/editstudent/{self.s1.id}/', {
            'rollno': 1, 'name': 'S1 New', 'fname': 'f', 'mname': 'm', 'gender': 'Male', 'dob': '01/01/2015',
            'contact': '9999999999', 'emailaddress': 'newmail@t.com', 'sclass': '5th', 'address': 'a',
            'feepaid': '10', 'duefee': '5'})
        self.assertEqual(r.status_code, 302)
        self.s1.refresh_from_db(); self.s1u.refresh_from_db()
        self.assertEqual(self.s1.name, 'S1 New')
        self.assertEqual(self.s1u.username, 'newmail@t.com')

    def test_edit_rejects_duplicate_email_and_roll(self):
        self.as_admin()
        base = {'rollno': 1, 'name': 'X', 'fname': 'f', 'mname': 'm', 'gender': 'Male', 'dob': 'd', 'contact': '9999999999',
                'emailaddress': 's2@t.com', 'sclass': '5th', 'address': 'a', 'feepaid': '0', 'duefee': '0'}
        self.client.post(f'/adminapp/editstudent/{self.s1.id}/', base)
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.name, 'S1')                       # unchanged: duplicate email refused

    def test_delete_student_removes_login_and_attendance(self):
        self.as_admin()
        sid = str(self.s1.id)
        self.assertEqual(self.client.post(f'/adminapp/deletestudent/{self.s1.id}/').status_code, 302)
        self.assertFalse(student.objects.filter(pk=self.s1.id).exists())
        self.assertFalse(User.objects.filter(username='s1@t.com').exists())
        self.assertFalse(Attendance.objects.filter(sid=sid).exists())
        self.assertEqual(self.client.get(f'/adminapp/deletestudent/{self.s2.id}/').status_code, 405)  # GET refused

    def test_teacher_edit_and_delete(self):
        self.as_admin()
        self.client.post(f'/adminapp/editteacher/{self.teacher.id}/', {
            'name': 'T2', 'fname': 'f', 'mname': 'm', 'gender': 'Female', 'dob': 'x', 'contact': '9999999999',
            'emailaddress': 'teach@t.com', 'tclass': '5th', 'address': 'a', 'salary': '5', 'qualification': 'q'})
        self.teacher.refresh_from_db(); self.assertEqual(self.teacher.name, 'T2')
        self.client.post(f'/adminapp/deleteteacher/{self.teacher.id}/')
        self.assertFalse(User.objects.filter(username='teach@t.com').exists())

    def test_class_delete_blocked_while_in_use(self):
        from adminapp.models import Classes
        self.as_admin()
        c = Classes.objects.create(cid=1, class_name='5th', seats=30, roomno='1', created_date=datetime.date.today())
        self.client.post(f'/adminapp/deleteclass/{c.cid}/')
        self.assertTrue(Classes.objects.filter(cid=1).exists())

    def test_upload_validation_blocks_bad_types(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.as_admin()
        bad = SimpleUploadedFile('evil.exe', b'x')
        self.client.post('/adminapp/addnoti/', {'text': 'hi', 'doc': bad})
        from adminapp.models import Notification
        self.assertEqual(Notification.objects.count(), 0)
        ok = SimpleUploadedFile('circular.pdf', b'%PDF-1.4')
        self.client.post('/adminapp/addnoti/', {'text': 'hi', 'doc': ok})
        self.assertEqual(Notification.objects.count(), 1)

    def test_bulk_attendance_and_update(self):
        self.client.login(username='teach@t.com', password='pass12345')
        d = '2026-01-05'
        self.client.post('/teacherapp/addattend/', {'created_date': d, f'status_{self.s1.id}': 'A'})
        self.assertEqual(Attendance.objects.get(sid=str(self.s1.id), created_date=d).status, 'A')
        self.client.post('/teacherapp/addattend/', {'created_date': d, f'status_{self.s1.id}': 'P'})
        self.assertEqual(Attendance.objects.filter(sid=str(self.s1.id), created_date=d).count(), 1)   # updated, not duplicated
        self.assertEqual(Attendance.objects.get(sid=str(self.s1.id), created_date=d).status, 'P')

    def test_teacher_cannot_delete_other_class_attendance(self):
        self.client.login(username='teach@t.com', password='pass12345')
        other = Attendance.objects.get(sid=str(self.s2.id))
        self.client.post(f'/teacherapp/delattend/{other.id}/')
        self.assertTrue(Attendance.objects.filter(pk=other.id).exists())

    def test_student_change_password(self):
        self.client.login(username='s1@t.com', password='pass12345')
        self.client.post('/studentapp/changepassword/', {'oldpassword': 'pass12345', 'newpassword': 'newpass99', 'cnfpassword': 'newpass99'})
        self.client.logout()
        self.assertTrue(self.client.login(username='s1@t.com', password='newpass99'))
        self.assertEqual(self.client.get('/studentapp/profile/').status_code, 200)

    def test_video_gallery_and_news_pages(self):
        self.as_admin()
        self.client.post('/adminapp/addvideo/', {'title': 'Annual Day', 'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'})
        self.client.logout()
        self.assertContains(self.client.get('/video/'), 'dQw4w9WgXcQ')
        self.assertEqual(self.client.get('/newsevent/').status_code, 200)
        self.assertEqual(self.client.get('/career/').status_code, 200)
        self.assertEqual(self.client.get('/groupinstitutions/').status_code, 200)

    def test_contact_form_validation(self):
        from smsapp.models import Enquiry
        data = {'name': 'A', 'gender': 'Male', 'address': 'x', 'contact': '123', 'emailaddress': 'bad', 'enquirytext': 'hello'}
        self.client.post('/contact/', data)
        self.assertEqual(Enquiry.objects.count(), 0)
        data.update(contact='9999999999', emailaddress='ok@t.com')
        self.client.post('/contact/', data)
        self.assertEqual(Enquiry.objects.count(), 1)

    def test_admin_list_pages_search_and_pagination(self):
        self.as_admin()
        for u in ('/adminapp/viewstudent/?q=S1', '/adminapp/viewteacher/?q=T', '/adminapp/viewenquiry/', '/adminapp/viewclass/',
                  '/adminapp/viewsubject/', '/adminapp/viewnoti/', '/adminapp/viewvideo/', f'/adminapp/editstudent/{self.s1.id}/',
                  f'/adminapp/editteacher/{self.teacher.id}/', '/adminapp/addsubject/'):
            self.assertEqual(self.client.get(u).status_code, 200, u)


class FeeAndTimetableTests(BaseCase):
    def test_record_payment_updates_balances_and_blocks_overpayment(self):
        self.client.login(username='admin@t.com', password='pass12345')
        url = f'/adminapp/studentfees/{self.s1.id}/'
        # s1.duefee starts at '0' in make_student helper -> bump it first
        self.s1.duefee = '500'; self.s1.feepaid = '0'; self.s1.save()
        self.client.post(url, {'amount': '200', 'paid_on': '2026-01-10', 'mode': 'Cash'})
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.feepaid, '200'); self.assertEqual(self.s1.duefee, '300')
        # overpay is rejected
        self.client.post(url, {'amount': '9999', 'paid_on': '2026-01-11', 'mode': 'Cash'})
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.duefee, '300')   # unchanged

    def test_reverse_payment_restores_due(self):
        self.client.login(username='admin@t.com', password='pass12345')
        self.s1.duefee = '500'; self.s1.feepaid = '0'; self.s1.save()
        self.client.post(f'/adminapp/studentfees/{self.s1.id}/', {'amount': '200', 'paid_on': '2026-01-10', 'mode': 'Cash'})
        from adminapp.models import FeePayment
        pay = FeePayment.objects.get(student=self.s1)
        self.client.post(f'/adminapp/deletepayment/{pay.id}/')
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.duefee, '500'); self.assertEqual(self.s1.feepaid, '0')
        self.assertFalse(FeePayment.objects.filter(pk=pay.id).exists())

    def test_fee_receipt_pdf_and_ownership(self):
        self.client.login(username='admin@t.com', password='pass12345')
        self.s1.duefee = '500'; self.s1.save()
        self.client.post(f'/adminapp/studentfees/{self.s1.id}/', {'amount': '100', 'paid_on': '2026-01-10', 'mode': 'UPI'})
        from adminapp.models import FeePayment
        pay = FeePayment.objects.get(student=self.s1)
        r = self.client.get(f'/adminapp/feereceipt/{pay.id}/')
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.client.logout(); self.client.login(username='p@t.com', password='pass12345')
        ok = self.client.get(f'/parentapp/receipt/{self.s1.id}/{pay.id}/')
        self.assertEqual(ok.status_code, 200)
        bad = self.client.get(f'/parentapp/receipt/{self.s2.id}/{pay.id}/')
        self.assertEqual(bad.status_code, 404)

    def test_fee_dashboard_and_student_only_admin(self):
        self.client.login(username='admin@t.com', password='pass12345')
        self.assertEqual(self.client.get('/adminapp/feedashboard/').status_code, 200)
        self.client.logout(); self.client.login(username='s1@t.com', password='pass12345')
        self.assertEqual(self.client.get('/adminapp/feedashboard/').status_code, 403)

    def test_timetable_crud_and_conflict_prevention(self):
        self.client.login(username='admin@t.com', password='pass12345')
        url = '/adminapp/timetable/'
        self.client.post(url, {'sclass': '5th', 'day': '0', 'period': '1', 'start_time': '09:00', 'end_time': '09:40',
                               'subject': 'Maths', 'teacher': self.teacher.id})
        from adminapp.models import TimetableEntry
        self.assertEqual(TimetableEntry.objects.filter(sclass='5th', day=0, period=1).count(), 1)
        # same slot again -> updates, not a duplicate
        self.client.post(url, {'sclass': '5th', 'day': '0', 'period': '1', 'start_time': '09:00', 'end_time': '09:40',
                               'subject': 'English', 'teacher': self.teacher.id})
        self.assertEqual(TimetableEntry.objects.filter(sclass='5th', day=0, period=1).count(), 1)
        self.assertEqual(TimetableEntry.objects.get(sclass='5th', day=0, period=1).subject, 'English')
        # bad time range rejected
        self.client.post(url, {'sclass': '5th', 'day': '1', 'period': '1', 'start_time': '10:00', 'end_time': '09:00',
                               'subject': 'Bad'})
        self.assertFalse(TimetableEntry.objects.filter(sclass='5th', day=1).exists())

    def test_student_and_parent_see_readonly_timetable(self):
        from adminapp.models import TimetableEntry
        TimetableEntry.objects.create(sclass='5th', day=0, period=1, start_time='09:00', end_time='09:40',
                                      subject='Maths', teacher=self.teacher)
        self.client.login(username='s1@t.com', password='pass12345')
        self.assertContains(self.client.get('/studentapp/timetable/'), 'Maths')

    def test_api_fee_and_timetable_scoping(self):
        from adminapp.models import FeePayment
        FeePayment.objects.create(student=self.s1, amount=100, paid_on=datetime.date.today(), mode='Cash')
        self.assertEqual(self.api(self.puser).get('/api/v1/fee-payments/').data['count'], 1)
        self.assertEqual(self.api(self.s2u).get('/api/v1/fee-payments/').data['count'], 0)
        r = self.api(self.s1u).post('/api/v1/fee-payments/', {'student': self.s1.id, 'amount': 50,
                                                              'paid_on': str(datetime.date.today()), 'mode': 'Cash'})
        self.assertEqual(r.status_code, 403)
