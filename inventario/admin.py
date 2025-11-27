# inventario/admin.py

from django.contrib import admin
from .models import (
    Herramienta,
    Docente,
    Estudiante,
    Asignatura,
    Panolero,
    Prestamo,
    PrestamoDetalle,
)

# ---------------------------------------------------
# HERRAMIENTAS
# ---------------------------------------------------
@admin.register(Herramienta)
class HerramientaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "tipo",
        "stock",
        "stock_disponible",
        "codigo_barra",
    )
    search_fields = (
        "codigo",
        "nombre",
        "codigo_barra",
    )
    list_filter = ("tipo",)
    ordering = ("codigo",)


# ---------------------------------------------------
# DOCENTES
# ---------------------------------------------------
@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activo")
    search_fields = ("codigo", "nombre")
    list_filter = ("activo",)
    ordering = ("codigo",)


# ---------------------------------------------------
# ESTUDIANTES
# ---------------------------------------------------
@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombre", "carrera", "activo")
    search_fields = ("rut", "nombre", "carrera")
    list_filter = ("activo",)
    ordering = ("rut",)


# ---------------------------------------------------
# ASIGNATURAS
# ---------------------------------------------------
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "nombre")
    search_fields = ("codigo", "nombre")
    ordering = ("nombre",)


# ---------------------------------------------------
# PANOLEROS
# ---------------------------------------------------
@admin.register(Panolero)
class PanoleroAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "nombre", "rol", "activo", "user")
    search_fields = ("codigo", "nombre", "user__username")
    list_filter = ("rol", "activo")
    ordering = ("codigo",)


# ---------------------------------------------------
# INLINES: DETALLE DE PRESTAMO
# ---------------------------------------------------
class PrestamoDetalleInline(admin.TabularInline):
    model = PrestamoDetalle
    extra = 0
    # Por si quieres evitar que borren desde aquí:
    # can_delete = False


# ---------------------------------------------------
# PRESTAMOS (CABECERA)
# ---------------------------------------------------
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_prestamo",
        "fecha",
        "hora_inicio",
        "hora_fin",
        "panolero",
        "docente",
        "estudiante",
        "asignatura",
        "estado",
    )
    list_filter = ("estado", "fecha", "panolero")
    search_fields = (
        "codigo_prestamo",
        "docente__nombre",
        "estudiante__nombre",
        "asignatura__nombre",
    )
    inlines = [PrestamoDetalleInline]
    ordering = ("-fecha", "-id")
