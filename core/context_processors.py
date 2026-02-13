from .models import Clinic


def clinic_context(request):
    if request.user.is_authenticated:
        return {
            "all_clinics": Clinic.objects.all(),
            "is_admin": request.user.is_staff,
            "is_front_desk": request.user.groups.filter(name="front_desk").exists(),
        }
    return {}
