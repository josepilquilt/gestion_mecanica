# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from inventario.models import Panolero  # importa Panolero si no estaba

@login_required
def menu_principal(request):
    user = request.user

    # ¿Es Docente? (grupo "Docente")
    es_docente = user.groups.filter(name="Docente").exists()

    # ¿Es pañolero?
    es_panolero = user.groups.filter(name="Pañolero").exists()

    # ¿Es jefatura según tabla Panolero?
    pan = Panolero.objects.filter(user=user, activo=True).first()
    es_jefe = False
    if pan and (pan.rol or "").lower() == "jefe":
        es_jefe = True

    context = {
        "es_docente": es_docente,
        "es_panolero": es_panolero,
        "es_jefe": es_jefe,
    }
    return render(request, "core/menu.html", context)

def logout_msg(request):
    return render(request, "core/logout_msg.html")
