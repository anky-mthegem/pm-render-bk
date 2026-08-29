from django import forms
from django.contrib.auth.models import User
from teams.models import Department, Team, TeamMembership


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'parent', 'head', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none',
                'placeholder': 'e.g. Engineering & Technology'
            }),
            'parent': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'head': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none',
                'rows': 2,
                'placeholder': 'Department purpose and objectives...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head'].queryset = User.objects.filter(is_active=True).exclude(username='aman').order_by('first_name', 'username')


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'department', 'parent_team', 'lead', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none',
                'placeholder': 'e.g. Core Platform Engineering'
            }),
            'department': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'parent_team': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'lead': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none',
                'type': 'color'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none',
                'rows': 3,
                'placeholder': 'Team responsibilities, domain, and focus areas...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead'].queryset = User.objects.filter(is_active=True).exclude(username='aman').order_by('first_name', 'username')


class TeamMembershipForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = ['team', 'user', 'role', 'reporting_to']
        widgets = {
            'team': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'user': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'role': forms.Select(choices=TeamMembership.ROLE_CHOICES, attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
            'reporting_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:ring-2 focus:ring-brand-500 focus:outline-none'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True).exclude(username='aman').order_by('first_name', 'username')
        self.fields['reporting_to'].queryset = User.objects.filter(is_active=True).exclude(username='aman').order_by('first_name', 'username')
