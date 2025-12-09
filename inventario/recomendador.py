# inventario/recomendador.py

from collections import defaultdict
import os
import csv

from django.db.models import Count
from django.conf import settings

from .models import (
    PreparacionDetalle,
    PrestamoDetalle,
    Asignatura,
    Herramienta,
)

# "Modelo" en memoria:
# { asignatura_id: [ {herramienta_id, nombre, score}, ... ] }
MODELO_RECOMENDACION = {}
TOP_GLOBAL_DEFAULT = []          # ranking global de herramientas
PESOS_EXCEL = {}                 # {(asig_id, herramienta_id): factor}

# Ruta de los CSV (ajusta si los tienes en otra carpeta)
BASE_DATA_DIR = os.path.join(settings.BASE_DIR, "data")
RUTA_PESOS = os.path.join(BASE_DATA_DIR, "pesos_herramientas_por_asignatura.csv")
RUTA_RANKING = os.path.join(BASE_DATA_DIR, "ranking_herramientas_uso_mecanica.csv")


def _float_safe(value, default=0.0):
    """Convierte a float de forma segura (acepta coma, vacíos, etc.)."""
    try:
        if value is None:
            return default
        s = str(value).strip().replace(",", ".")
        if not s:
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def _cargar_pesos_desde_excel():
    """
    Lee los 2 CSV y construye un diccionario:

        {(asignatura_id, herramienta_id): factor_peso}

    El factor combina:
      - 'nivel_uso' de ranking_herramientas_uso_mecanica.csv
      - 'Peso_sugerido_1a5' por Asignatura/Familia_herramienta
        de pesos_herramientas_por_asignatura.csv
    """
    global PESOS_EXCEL
    if PESOS_EXCEL:
        return PESOS_EXCEL

    # 1) ranking por código de herramienta (uso global y categoría/familia)
    ranking_por_codigo = {}
    if os.path.exists(RUTA_RANKING):
        with open(RUTA_RANKING, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo = (row.get("codigo") or "").strip()
                if not codigo:
                    continue
                nivel_uso = _float_safe(row.get("nivel_uso"), 0.0)
                categoria = (row.get("categoria") or "").strip()
                ranking_por_codigo[codigo] = {
                    "nivel_uso": nivel_uso,
                    "categoria": categoria,
                }

    # 2) pesos por (Asignatura, Familia_herramienta)
    pesos_asig_categoria = {}
    if os.path.exists(RUTA_PESOS):
        with open(RUTA_PESOS, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                asignatura_nombre = (row.get("Asignatura") or "").strip()
                familia = (row.get("Familia_herramienta") or "").strip()
                if not asignatura_nombre or not familia:
                    continue
                peso = _float_safe(row.get("Peso_sugerido_1a5"), 0.0)
                pesos_asig_categoria[(asignatura_nombre, familia)] = peso

    pesos = {}

    if not ranking_por_codigo and not pesos_asig_categoria:
        PESOS_EXCEL = pesos
        return pesos

    # Cache de asignaturas por nombre
    asignaturas_por_nombre = {}
    for asig in Asignatura.objects.all():
        asignaturas_por_nombre[asig.nombre.strip()] = asig

    herramientas = list(Herramienta.objects.all())

    # 3) Combinar para cada asignatura / herramienta
    for asig_nombre, asig in asignaturas_por_nombre.items():
        for h in herramientas:
            info_rank = ranking_por_codigo.get(str(h.codigo).strip())
            if not info_rank:
                continue

            categoria = info_rank["categoria"]
            nivel_uso = info_rank["nivel_uso"]  # 1–4 aprox
            peso_familia = pesos_asig_categoria.get((asig_nombre, categoria), 0.0)  # 1–5

            # Si no hay ninguna información, no aportamos nada
            if peso_familia == 0 and nivel_uso == 0:
                continue

            # Combinación sencilla:
            #   - 70% peso de la familia en esa asignatura (0–5)
            #   - 30% nivel de uso global (1–4)
            #   → factor alrededor de 1.x
            factor = 1.0 + (peso_familia / 5.0) * 0.7 + (nivel_uso / 4.0) * 0.3
            pesos[(asig.id, h.id)] = factor

    PESOS_EXCEL = pesos
    return pesos


def entrenar_modelo():
    """
    Entrena (o reentrena) el modelo de recomendación.

    - Usa histórico real (Preparaciones y Préstamos),
      excluyendo los préstamos sintéticos.
    - Ajusta los scores con los pesos de los 2 CSV.
    - Calcula un ranking global y un ranking por asignatura.
    """
    global MODELO_RECOMENDACION, TOP_GLOBAL_DEFAULT

    MODELO_RECOMENDACION = {}
    TOP_GLOBAL_DEFAULT = []

    # datos[asignatura_id][herramienta_id] = {nombre, score}
    datos = defaultdict(lambda: defaultdict(lambda: {"nombre": "", "score": 0.0}))
    # global_scores[herramienta_id] = {nombre, score}
    global_scores = defaultdict(lambda: {"nombre": "", "score": 0.0})

    pesos_excel = _cargar_pesos_desde_excel()

    # ============================
    # 1) HISTÓRICO DESDE PREPARACIONES
    # ============================
    prep_qs = (
        PreparacionDetalle.objects
        .filter(preparacion__asignatura__isnull=False)
        .values(
            "preparacion__asignatura_id",
            "herramienta_id",
            "herramienta__nombre",
        )
        .annotate(total_usos=Count("id"))
    )

    for row in prep_qs:
        asig_id = row["preparacion__asignatura_id"]
        h_id = row["herramienta_id"]
        if asig_id is None or h_id is None:
            continue

        nombre = row["herramienta__nombre"]
        usos = row["total_usos"] or 0

        factor = pesos_excel.get((asig_id, h_id), 1.0)
        score_inc = usos * factor

        # Por asignatura
        datos[asig_id][h_id]["nombre"] = nombre
        datos[asig_id][h_id]["score"] += score_inc

        # Global
        global_scores[h_id]["nombre"] = nombre
        global_scores[h_id]["score"] += score_inc

    # ============================
    # 2) HISTÓRICO DESDE PRÉSTAMOS (EXCLUIMOS SINTÉTICOS)
    # ============================
    prest_qs = (
        PrestamoDetalle.objects
        .filter(prestamo__asignatura__isnull=False)
        .exclude(prestamo__observaciones__icontains="sintético")
        .values(
            "prestamo__asignatura_id",
            "herramienta_id",
            "herramienta__nombre",
        )
        .annotate(total_usos=Count("id"))
    )

    for row in prest_qs:
        asig_id = row["prestamo__asignatura_id"]
        h_id = row["herramienta_id"]
        if asig_id is None or h_id is None:
            continue

        nombre = row["herramienta__nombre"]
        usos = row["total_usos"] or 0

        factor = pesos_excel.get((asig_id, h_id), 1.0)
        score_inc = usos * factor

        # Por asignatura
        datos[asig_id][h_id]["nombre"] = nombre
        datos[asig_id][h_id]["score"] += score_inc

        # Global
        global_scores[h_id]["nombre"] = nombre
        global_scores[h_id]["score"] += score_inc

    # ============================
    # 3) RANKING GLOBAL
    # ============================
    lista_global = []
    for h_id, info in global_scores.items():
        lista_global.append({
            "herramienta_id": h_id,
            "nombre": info["nombre"],
            "score": float(info["score"]),
        })
    lista_global.sort(key=lambda x: x["score"], reverse=True)
    TOP_GLOBAL_DEFAULT = lista_global

    # ============================
    # 4) RANKING POR ASIGNATURA
    #    (si no hay histórico, se usa el global)
    # ============================
    modelo_final = {}
    for asig in Asignatura.objects.all():
        asig_id = asig.id
        herramientas_dict = datos.get(asig_id)

        if herramientas_dict:
            lista = []
            for h_id, info in herramientas_dict.items():
                lista.append({
                    "herramienta_id": h_id,
                    "nombre": info["nombre"],
                    "score": float(info["score"]),
                })
            lista.sort(key=lambda x: x["score"], reverse=True)
            modelo_final[asig_id] = lista
        else:
            modelo_final[asig_id] = lista_global

    MODELO_RECOMENDACION = modelo_final


def construir_mapa_herramientas_por_asignatura():
    """
    Devuelve un dict:
      { asignatura_id: [herramienta_id, herramienta_id, ...] }

    La lista tiene repeticiones según las veces usadas,
    útil para generar datos sintéticos ponderados.
    """
    mapa = defaultdict(list)

    # Desde PREPARACIONES
    prep_qs = (
        PreparacionDetalle.objects
        .filter(preparacion__asignatura__isnull=False)
        .values("preparacion__asignatura_id", "herramienta_id")
        .annotate(total=Count("id"))
    )
    for row in prep_qs:
        asig_id = row["preparacion__asignatura_id"]
        h_id = row["herramienta_id"]
        if asig_id and h_id:
            mapa[asig_id].extend([h_id] * row["total"])

    # Desde PRÉSTAMOS (sin sintéticos)
    prest_qs = (
        PrestamoDetalle.objects
        .filter(prestamo__asignatura__isnull=False)
        .exclude(prestamo__observaciones__icontains="sintético")
        .values("prestamo__asignatura_id", "herramienta_id")
        .annotate(total=Count("id"))
    )
    for row in prest_qs:
        asig_id = row["prestamo__asignatura_id"]
        h_id = row["herramienta_id"]
        if asig_id and h_id:
            mapa[asig_id].extend([h_id] * row["total"])

    return dict(mapa)


def recomendar_herramientas(asignatura, top_n=10):
    """
    Devuelve una lista de hasta 'top_n' herramientas recomendadas para una asignatura.
    - 'asignatura' puede ser objeto Asignatura o un ID.
    - Si el modelo no está entrenado, se entrena en el momento.
    - Retorna lista de dicts: [{herramienta_id, nombre, score}, ...]
    """
    if isinstance(asignatura, Asignatura):
        asig_id = asignatura.id
    else:
        try:
            asig_id = int(asignatura)
        except (TypeError, ValueError):
            return []

    if not MODELO_RECOMENDACION:
        entrenar_modelo()

    lista = MODELO_RECOMENDACION.get(asig_id, TOP_GLOBAL_DEFAULT)
    return lista[:top_n]
