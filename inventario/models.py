# inventario/models.py

from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User


# ---------------------------------------
# HERRAMIENTAS  (YA EXISTE EN MYSQL)
# ---------------------------------------
class Herramienta(models.Model):
    codigo = models.CharField(max_length=20, primary_key=True)
    codigo_barra = models.CharField(max_length=50, blank=True)
    nombre = models.CharField(max_length=255)
    stock_disponible = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    tipo = models.CharField(max_length=50)

    class Meta:
        db_table = "herramientas"
        managed = False  # tabla creada a mano en MySQL

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    # ---------------------------------------
    # GENERAR CÓDIGO Y CÓDIGO DE BARRA
    # ---------------------------------------
    def save(self, *args, **kwargs):
        # Si no viene código, lo generamos
        if not self.codigo:
            # Tomamos el mayor código numérico
            ultimo = Herramienta.objects.aggregate(
                max_codigo=Max("codigo")
            )["max_codigo"]

            nuevo = 10000
            if ultimo:
                try:
                    num = int(ultimo)
                    # Solo si el último es >= 10000 seguimos desde ahí
                    if num >= 10000:
                        nuevo = num + 1
                except ValueError:
                    # Si hay códigos no numéricos, partimos en 10000
                    nuevo = 10000

            # Por seguridad, evitar colisiones
            while Herramienta.objects.filter(codigo=str(nuevo)).exists():
                nuevo += 1

            self.codigo = str(nuevo)

        # Si no hay código de barra, usar *codigo*
        if not self.codigo_barra:
            self.codigo_barra = f"*{self.codigo}*"

        # Si es nuevo registro y stock_disponible está en 0, igualarlo a stock
        if self._state.adding and self.stock_disponible == 0:
            self.stock_disponible = self.stock

        super().save(*args, **kwargs)


# ---------------------------------------
# DOCENTES (YA EXISTE EN MYSQL)
#   columnas: codigo (PK), nombre, activo
# ---------------------------------------
class Docente(models.Model):
    codigo = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "docentes"
        managed = False  # tabla creada por SQL

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# ---------------------------------------
# ESTUDIANTES  (NUEVA TABLA MYSQL)
#   rut = PK
# ---------------------------------------
class Estudiante(models.Model):
    rut = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=255)
    carrera = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "estudiantes"
        managed = False

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


# ---------------------------------------
# ASIGNATURAS  (NUEVA TABLA MYSQL)
# ---------------------------------------
class Asignatura(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = "asignaturas"
        managed = False

    def __str__(self):
        return self.nombre


# ---------------------------------------
# PANOLEROS  (NUEVA TABLA MYSQL)
#   Vinculado a auth_user
# ---------------------------------------
class Panolero(models.Model):
    ROL_CHOICES = [
        ('panolero', 'Pañolero'),
        ('jefe', 'Jefe de Pañol'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id")
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='panolero')
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "panoleros"
        managed = False

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# ---------------------------------------
# PRESTAMOS (CABECERA)
# ---------------------------------------
class Prestamo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('entregado', 'Entregado'),
        ('devuelto_parcial', 'Devuelto parcialmente'),
        ('devuelto', 'Devuelto'),
        ('anulado', 'Anulado'),
    ]

    id = models.AutoField(primary_key=True)
    codigo_prestamo = models.CharField(max_length=50, unique=True, db_index=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField(blank=True, null=True)

    panolero = models.ForeignKey(
        Panolero,
        on_delete=models.PROTECT,
        db_column="panolero_id",
        related_name="prestamos",
    )

    docente = models.ForeignKey(
        Docente,
        on_delete=models.PROTECT,
        db_column="docente_codigo",
        to_field="codigo",
        null=True,
        blank=True,
        related_name="prestamos",
    )

    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.PROTECT,
        db_column="estudiante_rut",
        to_field="rut",
        null=True,
        blank=True,
        related_name="prestamos",
    )

    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.SET_NULL,
        db_column="asignatura_id",
        null=True,
        blank=True,
        related_name="prestamos",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )

    observaciones = models.TextField(blank=True, null=True)

    # NUEVO: bitácora específica de devolución
    bitacora_devolucion = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at")

    class Meta:
        db_table = "prestamos"
        managed = False


# ---------------------------------------
# DETALLE DE PRESTAMO
#   - herramientas pedidas
#   - cantidades
# ---------------------------------------
class PrestamoDetalle(models.Model):
    id = models.AutoField(primary_key=True)

    prestamo = models.ForeignKey(
        Prestamo,
        on_delete=models.CASCADE,
        db_column="prestamo_id",
        related_name="detalles",
    )

    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        db_column="herramienta_codigo",
        to_field="codigo",
        related_name="prestamos_detalle",
    )

    # ojo: tu tabla tiene estas columnas
    cantidad_solicitada = models.IntegerField()
    cantidad_entregada = models.IntegerField()
    cantidad_devuelta = models.IntegerField(default=0)

    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "prestamo_detalle"
        managed = False

    def __str__(self):
        return (
            f"{self.herramienta} x {self.cantidad_solicitada} "
            f"(Préstamo {self.prestamo.codigo_prestamo})"
        )


# ---------------------------------------
# PREPARACIONES DE CLASE (CABECERA)
#   - similar a Prestamo, pero NO descuenta stock
# ---------------------------------------
class Preparacion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('usado', 'Entregado'),
        ('anulado', 'Anulado'),
    ]

    id = models.AutoField(primary_key=True)
    codigo_preparacion = models.CharField(max_length=50, unique=True, db_index=True)

    fecha = models.DateField()
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)  # ✅ NUEVO CAMPO

    panolero = models.ForeignKey(
        Panolero,
        on_delete=models.PROTECT,
        db_column="panolero_id",
        related_name="preparaciones",
    )

    docente = models.ForeignKey(
        Docente,
        on_delete=models.PROTECT,
        db_column="docente_codigo",
        to_field="codigo",
        null=True,
        blank=True,
        related_name="preparaciones",
    )

    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.SET_NULL,
        db_column="asignatura_id",
        null=True,
        blank=True,
        related_name="preparaciones",
    )

    observaciones = models.TextField(blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at")

    class Meta:
        db_table = "preparaciones"
        managed = False  # porque la creas tú en MySQL

    def __str__(self):
        return f"Prep {self.codigo_preparacion} ({self.fecha})"


# ---------------------------------------
# DETALLE DE PREPARACION
#   - herramientas pickeadas para la clase
# ---------------------------------------
class PreparacionDetalle(models.Model):
    id = models.AutoField(primary_key=True)

    preparacion = models.ForeignKey(
        Preparacion,
        on_delete=models.CASCADE,
        db_column="preparacion_id",
        related_name="detalles",
    )

    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        db_column="herramienta_codigo",
        to_field="codigo",
        related_name="preparaciones_detalle",
    )

    cantidad_solicitada = models.IntegerField()

    class Meta:
        db_table = "preparacion_detalle"
        managed = False

    def __str__(self):
        return f"{self.herramienta} x {self.cantidad_solicitada} (Prep {self.preparacion.codigo_preparacion})"


#----------------------------------------
#Bajas de herramientas 
#----------------------------------------
class Baja(models.Model):
    id = models.AutoField(primary_key=True)
    fecha_registro = models.DateField()
    hora_registro = models.TimeField(null=True, blank=True)
    panolero = models.ForeignKey(Panolero, on_delete=models.PROTECT, db_column="panolero_id")
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT,
                                db_column="docente_codigo", to_field="codigo",
                                null=True, blank=True)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.SET_NULL,
                                   db_column="asignatura_id",
                                   null=True, blank=True)
    fecha_clase = models.DateField(null=True, blank=True)
    hora_inicio_clase = models.TimeField(null=True, blank=True)
    seccion = models.CharField(max_length=50, blank=True, null=True)
    motivo_general = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "bajas"
        managed = False

class BajaDetalle(models.Model):
    id = models.AutoField(primary_key=True)

    baja = models.ForeignKey(
        Baja,
        on_delete=models.CASCADE,
        db_column="baja_id",
        related_name="detalles",   # para usar baja.detalles.all()
    )

    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        db_column="herramienta_codigo",
        to_field="codigo",
        related_name="bajas_detalle",
    )

    cantidad_baja = models.IntegerField()
    motivo = models.CharField(max_length=255, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "baja_detalle"
        managed = False
