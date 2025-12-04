# core/context_processors.py
from datetime import datetime
from django.utils import timezone

from inventario.models import Panolero, Preparacion


def notificaciones_panolero(request):
    """
    Agrega al contexto:
    - notif_30min_preps: preparaciones del día a ~30 minutos de iniciar
    - notif_5min_preps:  preparaciones del día a ~5 minutos de iniciar

    Solo aplica si el usuario logueado es pañolero activo.
    """
    if not request.user.is_authenticated:
        return {}

    # Buscar pañolero asociado al usuario
    panolero = Panolero.objects.filter(user=request.user, activo=True).first()
    if panolero is None:
        # Si no es pañolero, no hay notificaciones
        return {}

    now = timezone.localtime()  # datetime aware
    hoy = now.date()

    # Preparaciones pendientes de ese pañolero para hoy
    preps = (
        Preparacion.objects.filter(
            panolero=panolero,
            fecha=hoy,
            estado="pendiente",
        )
        .exclude(hora_inicio__isnull=True)
    )

    notif_5 = []
    notif_30 = []

    tz = timezone.get_current_timezone()

    for prep in preps:
        # Combinar fecha + hora_inicio en un datetime
        start_naive = datetime.combine(prep.fecha, prep.hora_inicio)
        # Lo hacemos aware con la zona horaria del proyecto
        start_dt = timezone.make_aware(start_naive, tz)

        delta_min = (start_dt - now).total_seconds() / 60.0

        # Solo nos interesan futuras (delta > 0)
        if delta_min <= 0:
            continue

        # Ventana de ~30 minutos antes (entre 25 y 35 min)
        if 25 <= delta_min <= 35:
            notif_30.append(prep)
        # Ventana de ~5 minutos antes (entre 0 y 5 min)
        elif 0 < delta_min <= 5:
            notif_5.append(prep)

    return {
        "notif_30min_preps": notif_30,
        "notif_5min_preps": notif_5,
    }
