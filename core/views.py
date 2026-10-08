from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import BicycleForm, MaintenanceForm, UnifiedUserForm
from .models import Bicycle, Maintenance, UnifiedUser

PAGE_SIZE = 20
FLEET_CHAIN_LIMIT = 240


# ---------------------------------------------------------------------------
# Helpers shared by the list pages
# ---------------------------------------------------------------------------

def _count_by(model, field):
    """{value: number of rows} for one column, e.g. {"available": 31, ...}."""
    rows = model.objects.values(field).annotate(n=Count("id")).order_by()
    return {row[field]: row["n"] for row in rows}


def _query_url(params):
    params = {key: value for key, value in params.items() if value}
    return f"?{urlencode(params)}" if params else "?"


def _pills(choices, counts, current, params, key):
    """Filter pills ("All" + one per choice) that keep the other active filters."""
    def url_for(value):
        return _query_url({**params, key: value})

    pills = [{
        "label": "All",
        "count": sum(counts.values()),
        "url": url_for(""),
        "active": not current,
    }]
    for value, label in choices:
        pills.append({
            "label": label,
            "count": counts.get(value, 0),
            "url": url_for(value),
            "active": current == value,
        })
    return pills


def _paginate(request, queryset, params):
    page_obj = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))
    page_qs = urlencode({key: value for key, value in params.items() if value})
    return page_obj, page_qs


def _clean_choice(value, choices):
    return value if value in dict(choices) else ""


def _safe_next(request, fallback):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return fallback


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def dashboard(request):
    # Fleet
    bike_counts = _count_by(Bicycle, "status")
    bicycle_count = sum(bike_counts.values())
    fleet = list(
        Bicycle.objects.only("id", "bike_code", "brand", "model", "status")
        .order_by("bike_code")[:FLEET_CHAIN_LIMIT]
    )
    fleet_legend = [
        {"value": value, "label": label, "count": bike_counts.get(value, 0)}
        for value, label in Bicycle.Status.choices
    ]

    most_ridden = list(
        Bicycle.objects.filter(total_rides__gt=0).order_by("-total_rides", "bike_code")[:5]
    )
    if most_ridden:
        peak = most_ridden[0].total_rides
        for bike in most_ridden:
            bike.rides_pct = max(4, round(bike.total_rides * 100 / peak))

    # Maintenance
    maint_counts = _count_by(Maintenance, "status")
    repair_legend = [
        {"value": value, "label": label, "count": maint_counts.get(value, 0)}
        for value, label in Maintenance.Status.choices
    ]
    open_statuses = [Maintenance.Status.PENDING, Maintenance.Status.IN_PROGRESS]
    open_count = sum(maint_counts.get(status, 0) for status in open_statuses)
    open_maintenance = (
        Maintenance.objects.filter(status__in=open_statuses)
        .select_related("bicycle", "reported_by")
        .annotate(
            waiting_rank=Case(
                When(status=Maintenance.Status.PENDING, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("waiting_rank", "created_at")[:6]
    )
    repair_cost = (
        Maintenance.objects.filter(status=Maintenance.Status.COMPLETED)
        .aggregate(total=Sum("cost"))["total"]
        or 0
    )

    # Users
    role_counts = _count_by(UnifiedUser, "role")
    user_status_counts = _count_by(UnifiedUser, "status")
    role_legend = [
        {"value": value, "label": label, "count": role_counts.get(value, 0)}
        for value, label in UnifiedUser.Role.choices
    ]

    context = {
        "bicycle_count": bicycle_count,
        "available_bikes": bike_counts.get(Bicycle.Status.AVAILABLE, 0),
        "fleet": fleet,
        "fleet_hidden": max(0, bicycle_count - len(fleet)),
        "fleet_legend": fleet_legend,
        "most_ridden": most_ridden,
        "maintenance_count": sum(maint_counts.values()),
        "open_maintenance": open_maintenance,
        "open_count": open_count,
        "repair_legend": repair_legend,
        "repair_cost": repair_cost,
        "user_count": sum(role_counts.values()),
        "role_legend": role_legend,
        "suspended_users": user_status_counts.get(UnifiedUser.Status.SUSPENDED, 0),
    }
    return render(request, "core/dashboard.html", context)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def users(request):
    q = request.GET.get("q", "").strip()
    role = _clean_choice(request.GET.get("role", ""), UnifiedUser.Role.choices)
    status = _clean_choice(request.GET.get("status", ""), UnifiedUser.Status.choices)

    rows = UnifiedUser.objects.all()
    if q:
        rows = rows.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(student_id__icontains=q)
        )
    if role:
        rows = rows.filter(role=role)
    if status:
        rows = rows.filter(status=status)

    params = {"q": q, "role": role, "status": status}
    page_obj, page_qs = _paginate(request, rows, params)
    chips = []
    if status:
        chips.append({
            "label": f"Status: {dict(UnifiedUser.Status.choices)[status]}",
            "clear_url": _query_url({**params, "status": ""}),
        })

    context = {
        "page_obj": page_obj,
        "page_qs": page_qs,
        "q": q,
        "pills": _pills(UnifiedUser.Role.choices, _count_by(UnifiedUser, "role"), role, params, "role"),
        "chips": chips,
        "hidden_params": [("role", role), ("status", status)],
        "filtered": bool(q or role or status),
        "total": UnifiedUser.objects.count(),
    }
    return render(request, "core/users/list.html", context)


def user_create(request):
    form = UnifiedUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "User added.")
        return redirect("users")
    return render(request, "core/users/form.html", {"form": form, "title": "Add user"})


# ---------------------------------------------------------------------------
# Bicycles
# ---------------------------------------------------------------------------

def bicycles(request):
    q = request.GET.get("q", "").strip()
    status = _clean_choice(request.GET.get("status", ""), Bicycle.Status.choices)

    rows = Bicycle.objects.all()
    if q:
        rows = rows.filter(
            Q(bike_code__icontains=q)
            | Q(brand__icontains=q)
            | Q(model__icontains=q)
            | Q(color__icontains=q)
            | Q(current_location__icontains=q)
        )
    if status:
        rows = rows.filter(status=status)

    params = {"q": q, "status": status}
    page_obj, page_qs = _paginate(request, rows, params)

    context = {
        "page_obj": page_obj,
        "page_qs": page_qs,
        "q": q,
        "pills": _pills(Bicycle.Status.choices, _count_by(Bicycle, "status"), status, params, "status"),
        "chips": [],
        "hidden_params": [("status", status)],
        "filtered": bool(q or status),
        "total": Bicycle.objects.count(),
    }
    return render(request, "core/bicycles/list.html", context)


def bicycle_create(request):
    form = BicycleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Bicycle added.")
        return redirect("bicycles")
    return render(request, "core/bicycles/form.html", {"form": form, "title": "Add bicycle"})


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

def maintenance_list(request):
    q = request.GET.get("q", "").strip()
    status = _clean_choice(request.GET.get("status", ""), Maintenance.Status.choices)

    rows = Maintenance.objects.select_related("bicycle", "reported_by")
    if q:
        rows = rows.filter(
            Q(bicycle__bike_code__icontains=q)
            | Q(description__icontains=q)
            | Q(reported_by__first_name__icontains=q)
            | Q(reported_by__last_name__icontains=q)
        )
    if status:
        rows = rows.filter(status=status)

    params = {"q": q, "status": status}
    page_obj, page_qs = _paginate(request, rows, params)

    context = {
        "page_obj": page_obj,
        "page_qs": page_qs,
        "q": q,
        "pills": _pills(Maintenance.Status.choices, _count_by(Maintenance, "status"), status, params, "status"),
        "chips": [],
        "hidden_params": [("status", status)],
        "filtered": bool(q or status),
        "total": Maintenance.objects.count(),
    }
    return render(request, "core/maintenance/list.html", context)


def maintenance_create(request):
    form = MaintenanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        record = form.save()
        record.bicycle.status = Bicycle.Status.UNDER_MAINTENANCE
        record.bicycle.save(update_fields=["status", "updated_at"])
        messages.success(request, "Maintenance reported.")
        return redirect("maintenance")
    return render(request, "core/maintenance/form.html", {"form": form, "title": "Report maintenance"})


@require_POST
def maintenance_update_status(request, pk, status):
    record = get_object_or_404(Maintenance, pk=pk)
    back = _safe_next(request, "maintenance")
    valid = dict(Maintenance.Status.choices)
    if status not in valid:
        messages.error(request, "That status doesn't exist.")
        return redirect(back)

    record.status = status
    record.save(update_fields=["status", "updated_at"])

    if status in (Maintenance.Status.COMPLETED, Maintenance.Status.CANCELLED):
        record.bicycle.status = Bicycle.Status.AVAILABLE
    else:
        record.bicycle.status = Bicycle.Status.UNDER_MAINTENANCE
    record.bicycle.save(update_fields=["status", "updated_at"])

    messages.success(request, f"{record.bicycle.bike_code} marked {valid[status]}.")
    return redirect(back)
