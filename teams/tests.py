from django.test import TestCase, Client
from django.contrib.auth.models import User
from teams.models import Department, Team, TeamMembership
from projects.models import Project


class TeamManagerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='aman',
            email='aman@example.com',
            password='password123'
        )
        self.manager_user = User.objects.create_user(
            username='sundar',
            first_name='Sundar',
            last_name='Nadar',
            email='sundar@example.com',
            password='password123'
        )
        self.dev_user = User.objects.create_user(
            username='suraj',
            first_name='Suraj',
            last_name='',
            email='suraj@example.com',
            password='password123'
        )
        self.client.force_login(self.admin_user)

    def test_department_and_subdepartment_creation(self):
        parent_dept = Department.objects.create(
            name='Engineering',
            code='eng',
            head=self.manager_user
        )
        sub_dept = Department.objects.create(
            name='Platform Engineering',
            code='platform',
            parent=parent_dept
        )
        self.assertEqual(sub_dept.parent, parent_dept)
        self.assertEqual(str(sub_dept), "Engineering / Platform Engineering")

    def test_team_and_subteam_hierarchy(self):
        dept = Department.objects.create(name='Technology', code='tech')
        parent_team = Team.objects.create(
            name='Core Engineering',
            code='core-eng',
            department=dept,
            lead=self.manager_user
        )
        sub_team = Team.objects.create(
            name='Backend Services',
            code='backend-svc',
            department=dept,
            parent_team=parent_team,
            lead=self.manager_user
        )
        self.assertEqual(sub_team.parent_team, parent_team)
        self.assertEqual(parent_team.sub_teams.count(), 1)

    def test_membership_and_reporting_lines(self):
        dept = Department.objects.create(name='Tech', code='tech-dept')
        team = Team.objects.create(name='Dev Team', code='dev-team', department=dept, lead=self.manager_user)
        
        m_lead = TeamMembership.objects.create(
            team=team,
            user=self.manager_user,
            role='Lead',
            reporting_to=None
        )
        m_dev = TeamMembership.objects.create(
            team=team,
            user=self.dev_user,
            role='Senior Developer',
            reporting_to=self.manager_user
        )

        self.assertEqual(team.members_count, 2)
        self.assertEqual(m_dev.reporting_to, self.manager_user)
        self.assertEqual(m_lead.direct_reports_count, 1)

    def test_hierarchy_api_excludes_aman(self):
        dept = Department.objects.create(name='Engineering', code='eng-api', head=self.manager_user)
        team = Team.objects.create(name='API Team', code='api-team', department=dept, lead=self.manager_user)
        TeamMembership.objects.create(team=team, user=self.dev_user, role='Developer')

        res = self.client.get('/teams/api/hierarchy/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('departments', data)
        self.assertTrue(len(data['departments']) > 0)
        self.assertEqual(data['departments'][0]['name'], 'Engineering')
        # Ensure aman is not present in teams or members
        for d in data['departments']:
            for t in d['teams']:
                self.assertNotEqual(t['lead']['username'], 'aman')
                for m in t['members']:
                    self.assertNotEqual(m['username'], 'aman')

    def test_org_chart_api_response(self):
        dept = Department.objects.create(name='Engineering', code='eng-org')
        team = Team.objects.create(name='Core Team', code='core-team', department=dept, lead=self.manager_user)
        TeamMembership.objects.create(team=team, user=self.manager_user, role='Lead', reporting_to=None)
        TeamMembership.objects.create(team=team, user=self.dev_user, role='Senior Developer', reporting_to=self.manager_user)

        res = self.client.get('/teams/api/org-chart/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('nodes', data)
        # Verify aman is excluded from org chart nodes
        node_usernames = [n['username'] for n in data['nodes']]
        self.assertNotIn('aman', node_usernames)
        self.assertIn('sundar', node_usernames)
        self.assertIn('suraj', node_usernames)

    def test_update_reporting_api(self):
        dept = Department.objects.create(name='Ops', code='ops-dept')
        team = Team.objects.create(name='Ops Team', code='ops-team', department=dept)
        TeamMembership.objects.create(team=team, user=self.dev_user, role='Developer')

        res = self.client.post(
            '/teams/api/update-reporting/',
            data='{"user_id": ' + str(self.dev_user.id) + ', "reporting_to_id": ' + str(self.manager_user.id) + '}',
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'success')
        
        m = TeamMembership.objects.get(team=team, user=self.dev_user)
        self.assertEqual(m.reporting_to_id, self.manager_user.id)

    def test_project_team_link(self):
        dept = Department.objects.create(name='Dev', code='dev-proj')
        team = Team.objects.create(name='Alpha Team', code='alpha-team', department=dept)
        project = Project.objects.create(name='Project Alpha', code='alpha-prj', owner=self.admin_user, assigned_team=team)

        self.assertEqual(project.assigned_team, team)
        self.assertEqual(team.assigned_projects.first(), project)
