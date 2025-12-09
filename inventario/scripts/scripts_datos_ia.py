import random
from datetime import date, timedelta, time

from django.db import transaction
from inventario.models import (
    Prestamo,
    PrestamoDetalle,
    Asignatura,
    Herramienta,
    Docente,
    Panolero,
)
from inventario import recomendador as rec


def generar_prestamos_sinteticos(n_pedidos=1000):
    """
    Genera n_pedidos históricos sintéticos de préstamos,
    usando las herramientas más usadas por asignatura (modelo IA).
    NO toca stock; solo crea Prestamo y PrestamoDetalle.
    """

    # 1) Entrenar modelo y construir mapa asignatura → herramientas usadas
    rec.entrenar_modelo()
    try:
        mapa = rec.construir_mapa_herramientas_por_asignatura()
    except AttributeError:
        print(
            "ERROR: asegurate de tener definida la función "
            "construir_mapa_herramientas_por_asignatura en recomendador.py"
        )
        return

    asig_ids = list(mapa.keys())
    if not asig_ids:
        print("No hay asignaturas con datos históricos suficientes.")
        return

    panoleros = list(Panolero.objects.filter(activo=True))
    docentes = list(Docente.objects.filter(activo=True))

    if not panoleros:
        print("No hay pañoleros activos. No se puede generar datos.")
        return
    if not docentes:
        print("No hay docentes activos. No se puede generar datos.")
        return

    # Rango de fechas históricas (AJUSTABLE)
    fecha_inicio = date(2025, 4, 1)
    fecha_fin = date(2025, 11, 25)
    dias_rango = (fecha_fin - fecha_inicio).days

    print(f"Generando {n_pedidos} préstamos sintéticos entre {fecha_inicio} y {fecha_fin}...")

    with transaction.atomic():
        for i in range(n_pedidos):
            # 1) Elegir asignatura según las que tienen historial
            asig_id = random.choice(asig_ids)
            asignatura = Asignatura.objects.get(id=asig_id)

            # 2) Elegir pañolero y docente activos
            panolero = random.choice(panoleros)
            docente = random.choice(docentes)

            # 3) Fecha aleatoria dentro del rango
            offset = random.randint(0, dias_rango)
            fecha = fecha_inicio + timedelta(days=offset)

            # 4) Hora de inicio/fin de la clase
            hora_inicio = time(
                hour=random.randint(8, 21),
                minute=random.choice([0, 15, 30, 45]),
            )
            hora_fin = time(
                hour=min(hora_inicio.hour + random.randint(1, 3), 22),
                minute=hora_inicio.minute,
            )

            # 5) Código de préstamo tipo PYYYYMMDDhhmmssXXX
            codigo_prestamo = (
                "P"
                + fecha.strftime("%Y%m%d")
                + f"{hora_inicio.hour:02d}{hora_inicio.minute:02d}"
                + f"{i:03d}"
            )

            prestamo = Prestamo.objects.create(
                codigo_prestamo=codigo_prestamo,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                panolero=panolero,
                docente=docente,
                asignatura=asignatura,
                estado="devuelto",
                observaciones="[SINTÉTICO IA]",
            )

            # 6) Herramientas sugeridas para esa asignatura
            codigos_candidatos = list(mapa[asig_id])  # lista con repeticiones

            if len(codigos_candidatos) < 5:
                todas = list(Herramienta.objects.values_list("codigo", flat=True))
                codigos_candidatos = codigos_candidatos + todas

            # 7) Elegimos entre 3 y 8 herramientas diferentes para este préstamo
            num_lineas = random.randint(3, 8)
            herramientas_elegidas = set()
            intentos = 0

            while len(herramientas_elegidas) < num_lineas and intentos < num_lineas * 5:
                intentos += 1
                codigo_h = random.choice(codigos_candidatos)
                herramientas_elegidas.add(codigo_h)

            # 8) Crear PrestamoDetalle para cada herramienta
            for codigo_h in herramientas_elegidas:
                try:
                    herramienta = Herramienta.objects.get(codigo=codigo_h)
                except Herramienta.DoesNotExist:
                    continue

                cantidad = random.randint(1, 5)

                PrestamoDetalle.objects.create(
                    prestamo=prestamo,
                    herramienta=herramienta,
                    cantidad_solicitada=cantidad,
                    cantidad_entregada=cantidad,
                    cantidad_devuelta=cantidad,
                )

            if (i + 1) % 100 == 0:
                print(f"  → Generados {i+1} préstamos...")

    print(f"Listo. Se generaron {n_pedidos} préstamos sintéticos.")
