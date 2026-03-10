"""Dashboard views — HTMX-powered frontend."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import UserProfile
from apps.projects.models import Handoff, Project, Session


def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")
    return redirect("account_login")


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.org is None:
        from apps.accounts.models import Organization
        org = Organization.objects.create(
            name=f"{request.user.email}'s org",
            slug=f"user-{request.user.pk}",
            owner=request.user,
        )
        profile.org = org
        profile.save(update_fields=["org"])

    projects = Project.objects.filter(org=profile.org)
    total_sessions = Session.objects.filter(project__org=profile.org).count()
    total_handoffs = Handoff.objects.filter(session__project__org=profile.org).count()

    return render(request, "dashboard/index.html", {
        "projects": projects,
        "total_sessions": total_sessions,
        "total_handoffs": total_handoffs,
        "profile": profile,
    })


@login_required
def project_detail(request, project_id):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    project = get_object_or_404(Project, project_id=project_id, org=profile.org)
    sessions = Session.objects.filter(project=project)
    recent_handoffs = Handoff.objects.filter(session__project=project).order_by("-created_at")[:10]

    return render(request, "dashboard/project_detail.html", {
        "project": project,
        "sessions": sessions,
        "recent_handoffs": recent_handoffs,
    })


@login_required
def session_detail(request, project_id, session_id):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    project = get_object_or_404(Project, project_id=project_id, org=profile.org)
    session = get_object_or_404(Session, session_id=session_id, project=project)
    handoffs = Handoff.objects.filter(session=session).order_by("-version")

    return render(request, "dashboard/session_detail.html", {
        "project": project,
        "session": session,
        "handoffs": handoffs,
    })
