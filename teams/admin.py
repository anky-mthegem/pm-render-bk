from django.contrib import admin
from teams.models import Department, Team, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1
    autocomplete_fields = ['user', 'reporting_to']
    fields = ('user', 'role', 'reporting_to', 'joined_at')


class SubTeamInline(admin.TabularInline):
    model = Team
    fk_name = 'parent_team'
    extra = 0
    fields = ('name', 'lead', 'color')
    show_change_link = True


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent', 'head', 'total_members_display', 'created_at')
    search_fields = ('name', 'code', 'description')
    list_filter = ('parent',)
    autocomplete_fields = ['head', 'parent']

    def total_members_display(self, obj):
        return f"{obj.total_members_count} members"
    total_members_display.short_description = "Total Members"


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'parent_team', 'lead', 'members_count_display', 'color_badge')
    search_fields = ('name', 'code', 'description', 'lead__username', 'lead__first_name', 'lead__last_name')
    list_filter = ('department', 'parent_team')
    autocomplete_fields = ['lead', 'department', 'parent_team']
    inlines = [SubTeamInline, TeamMembershipInline]

    def members_count_display(self, obj):
        return f"{obj.members_count} members"
    members_count_display.short_description = "Members"

    def color_badge(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            obj.color,
            obj.color
        )
    color_badge.short_description = "Color"


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'reporting_to', 'joined_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'team__name', 'role')
    list_filter = ('team', 'role', 'team__department')
    autocomplete_fields = ['user', 'team', 'reporting_to']
