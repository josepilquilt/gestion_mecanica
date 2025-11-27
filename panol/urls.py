from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from inventario import views as inventario_views

urlpatterns = [
    #Admin django
    path('admin/', admin.site.urls),
    #Menu principal
    path('', core_views.menu_principal, name='menu_principal'),

    # Inventario


    #lista de las herraminetas
    path('inventario/', inventario_views.lista_herramientas, name='lista_herramientas'),  
    #Pagina para crear herramineta y sumar stock
    path('inventario/gestionar/', inventario_views.gestionar_herramienta, name='gestionar_herramienta'),
    #Apis de inventario , para consultas AJAX(busqueda del codigo de la herramienta
    #Buscar herraminetas por codigo(usado en prestamos y preparaciones)
    path("inventario/api/herramienta/", inventario_views.api_herramienta_por_codigo, name="api_herramienta_por_codigo"),
    #Buscar preparacion por codigo(para cargar en Registrar prestamo)
    path("inventario/api/preparacion/", inventario_views.api_preparacion_por_codigo, name="api_preparacion_por_codigo"), 

    # Préstamos

    #listado prestamos
    path('prestamos/', inventario_views.lista_prestamos, name='lista_prestamos'),
    #Registrar prestamo
    path('prestamos/crear/', inventario_views.crear_prestamo, name='crear_prestamo'),
    #Registrar devolucion de prestamo
    path('prestamos/devolver/<int:prestamo_id>/', inventario_views.registrar_devolucion, name='registrar_devolucion'),

    

    
    #path("inventario/api/herramienta/", inventario_views.api_herramienta_por_codigo, name="api_herramienta_por_codigo"),

    #Preparacion clase
    
    #listado de preparaciones (picking previo)
    path("preparaciones/", inventario_views.lista_preparaciones, name="lista_preparaciones"),
    #crear una nueva preparacion
    path("preparaciones/crear/", inventario_views.crear_preparacion, name="crear_preparacion"), 
    #Nuuevos
    #ver detalle completo de una preparacion (ver Docente, herramientas , etc)
    path('preparaciones/<int:prep_id>/', inventario_views.detalle_preparacion, name='detalle_preparacion'),
    # Anular una preparacion
    path('preparaciones/<int:prep_id>/anular/', inventario_views.anular_preparacion, name='anular_preparacion'),

    #Baja herramientas 
    # 🔽🔽 NUEVO: registrar bajas desde un préstamo
     path('bajas/registrar/', inventario_views.registrar_baja, name='registrar_baja'),

    # 🔽🔽 NUEVO: listado de bajas
    path('bajas/', inventario_views.lista_bajas, name='lista_bajas'),


    # ---------------------------------------------------------
    # 📌 AUTENTICACIÓN (login / logout / password reset)
    # ---------------------------------------------------------
    path("accounts/", include("django.contrib.auth.urls")),
    path('logout-msg/', core_views.logout_msg, name='logout_msg'),
    #path("logout-msg/", core_views.logout_msg, name="logout_msg"),    


    #api codigo prestamo 
    path('prestamos/api/', inventario_views.api_prestamo_por_codigo,name='api_prestamo_por_codigo'),

    #Detalle baja 
    path('bajas/<int:baja_id>/', inventario_views.detalle_baja, name='detalle_baja'),

    # INFORMES
    path('informes/prestamos/', inventario_views.informe_prestamos, name='informe_prestamos'),

    path("informes/panel/", inventario_views.panel_kpis, name="panel_kpis"),

    path("informes/panel/exportar/", inventario_views.exportar_panel_kpis, name="exportar_panel_kpis",),
    


]
