from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=120, db_index=True)
    code = models.SlugField(max_length=64, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_departments'
    )
    description = models.TextField(blank=True, default='')
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            base = slugify(self.name)[:50] or 'dept'
            cand = base
            i = 1
            while Department.objects.filter(code=cand).exclude(pk=self.pk).exists():
                cand = f"{base}-{i}"
                i += 1
            self.code = cand
        super().save(*args, **kwargs)

    @property
    def total_members_count(self):
        return sum(t.memberships.count() for t in self.teams.all())


class Team(models.Model):
    name = models.CharField(max_length=120, db_index=True)
    code = models.SlugField(max_length=64, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teams'
    )
    parent_team = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_teams'
    )
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_teams'
    )
    color = models.CharField(max_length=20, default='#6366f1', help_text="Badge hex color for UI cards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        if self.department:
            return f"[{self.department.name}] {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            base = slugify(self.name)[:50] or 'team'
            cand = base
            i = 1
            while Team.objects.filter(code=cand).exclude(pk=self.pk).exists():
                cand = f"{base}-{i}"
                i += 1
            self.code = cand
        super().save(*args, **kwargs)

    @property
    def members_count(self):
        return self.memberships.count()

    @property
    def direct_members(self):
        return self.memberships.select_related('user', 'reporting_to').all()

    @property
    def active_projects(self):
        return self.assigned_projects.filter(status='ACTIVE')


class TeamMembership(models.Model):
    ROLE_CHOICES = [
        ('Lead', 'Team Lead / Manager'),
        ('Tech Lead', 'Technical Lead / Architect'),
        ('Senior Developer', 'Senior Developer'),
        ('Developer', 'Software Engineer'),
        ('UI/UX Designer', 'UI/UX Designer'),
        ('Product Manager', 'Product Manager'),
        ('QA Engineer', 'QA / Automation Engineer'),
        ('DevOps Engineer', 'DevOps / SRE Engineer'),
        ('Business Analyst', 'Business Analyst'),
        ('Member', 'Team Contributor / Member'),
    ]

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    role = models.CharField(max_length=64, choices=ROLE_CHOICES, default='Member')
    reporting_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports'
    )
    joined_at = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['role', 'user__first_name']
        constraints = [
            models.UniqueConstraint(fields=['team', 'user'], name='unique_team_user_membership')
        ]
        verbose_name = 'Team Membership'
        verbose_name_plural = 'Team Memberships'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role} ({self.team.name})"

    @property
    def direct_reports_count(self):
        return TeamMembership.objects.filter(reporting_to=self.user).count()
