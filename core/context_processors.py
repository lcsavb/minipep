from .models import Clinic


def clinic_context(request):
    if request.user.is_authenticated:
        return {"all_clinics": Clinic.objects.all()}
    return {}
