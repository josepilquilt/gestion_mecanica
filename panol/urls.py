from django.contrib import admin
from django.urls import path, include

from core import views as core_views
from inventario import views as inventario_views

urlpatterns = [
    # ---------------------------------------------------------
    # ADMIN DJANGO
    # ---------------------------------------------------------
    path('admin/', admin.site.urls),

    # ---------------------------------------------------------
    # MENÚ PRINCIPAL
    # ---------------------------------------------------------
    path('', core_views.menu_principal, name='menu_principal'),

    # ---------------------------------------------------------
    # ADMINISTRACIÓN DE USUARIOS (solo Jefe de Pañol)
    # Vista: inventario_views.administracion
    # Template: inventario/administracion.html
    # ---------------------------------------------------------
    path('administracion/', inventario_views.administracion, name='administracion'),

    # ---------------------------------------------------------
    # MÓDULO INVENTARIO
    # ---------------------------------------------------------
    # Listado de herramientas
    path('inventario/', inventario_views.lista_herramientas, name='lista_herramientas'),

    # Crear herramienta y sumar stock
    path('inventario/gestionar/', inventario_views.gestionar_herramienta, name='gestionar_herramienta'),

    # API: buscar herramienta por código o código de barra (uso en AJAX)
    path('inventario/api/herramienta/', inventario_views.api_herramienta_por_codigo,
         name='api_herramienta_por_codigo'),

    # API: buscar preparación por código (para cargar en crear_prestamo)
    path('inventario/api/preparacion/', inventario_views.api_preparacion_por_codigo,
         name='api_preparacion_por_codigo'),

    # ---------------------------------------------------------
    # MÓDULO PRÉSTAMOS
    # ---------------------------------------------------------
    # Listado de préstamos
    path('prestamos/', inventario_views.lista_prestamos, name='lista_prestamos'),

    # Registrar préstamo (salida)
    path('prestamos/crear/', inventario_views.crear_prestamo, name='crear_prestamo'),

    # Registrar devolución de préstamo
    path('prestamos/devolver/<int:prestamo_id>/',
         inventario_views.registrar_devolucion,
         name='registrar_devolucion'),

    # API: obtener préstamo por código (para módulo de bajas, etc.)
    path('prestamos/api/', inventario_views.api_prestamo_por_codigo,
         name='api_prestamo_por_codigo'),

    # ---------------------------------------------------------
    # MÓDULO PREPARACIONES DE CLASE (PICKING ANTICIPADO)
    # ---------------------------------------------------------
    # Listado de preparaciones
    path('preparaciones/', inventario_views.lista_preparaciones, name='lista_preparaciones'),

    # Crear nueva preparación de clase
    path('preparaciones/crear/', inventario_views.crear_preparacion, name='crear_preparacion'),

    # Ver detalle completo de una preparación
    path('preparaciones/<int:prep_id>/', inventario_views.detalle_preparacion,
         name='detalle_preparacion'),

    # Anular una preparación (devuelve stock_disponible si estaba pendiente)
    path('preparaciones/<int:prep_id>/anular/', inventario_views.anular_preparacion,
         name='anular_preparacion'),

    # ---------------------------------------------------------
    # MÓDULO BAJAS DE HERRAMIENTAS
    # ---------------------------------------------------------
    # Registrar bajas independientes
    path('bajas/registrar/', inventario_views.registrar_baja, name='registrar_baja'),

    # Listado de bajas
    path('bajas/', inventario_views.lista_bajas, name='lista_bajas'),

    # Detalle de una baja específica
    path('bajas/<int:baja_id>/', inventario_views.detalle_baja, name='detalle_baja'),

    # ---------------------------------------------------------
    # AUTENTICACIÓN (login / logout / reset password)
    # Usa las vistas genéricas de django.contrib.auth
    # ---------------------------------------------------------
    path('accounts/', include('django.contrib.auth.urls')),

    # Página de mensaje de logout (vista propia en core)
    path('logout-msg/', core_views.logout_msg, name='logout_msg'),

    # ---------------------------------------------------------
    # INFORMES Y KPIs
    # ---------------------------------------------------------
    # Informe detallado de préstamos
    path('informes/prestamos/', inventario_views.informe_prestamos,
         name='informe_prestamos'),

    # Panel de KPIs (dashboard)
    path('informes/panel/', inventario_views.panel_kpis, name='panel_kpis'),

    # Exportar KPIs (Excel / PDF)
    path('informes/panel/exportar/', inventario_views.exportar_panel_kpis,
         name='exportar_panel_kpis'),
]
