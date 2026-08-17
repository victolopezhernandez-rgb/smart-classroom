"""
La hora del salón.

El aula está en Colombia, pero el servidor de Render corre en UTC. Con
`datetime.now()` a secas el gemelo cree que son cinco horas más tarde: a la
una de la tarde el sol simulado ya se puso, la luz natural queda en 0.0 y la
IA enciende todo — justo lo contrario de lo que el proyecto quiere mostrar.

Todo lo que dependa de «qué hora es en el salón» debe pasar por aquí, no por
datetime.now(). Si algún día el aula se muda de país, se cambia CLASSROOM_TZ
y no hay que tocar nada más.
"""

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Se puede sobreescribir con la variable de entorno CLASSROOM_TZ.
_TZ_NAME = os.getenv("CLASSROOM_TZ", "America/Bogota")

try:
    CLASSROOM_TZ = ZoneInfo(_TZ_NAME)
except ZoneInfoNotFoundError:
    # Algunas imágenes de servidor vienen sin la base de zonas horarias. Antes
    # que tumbar el arranque, se cae a UTC-5, que es Colombia todo el año
    # (aquí no se cambia la hora en invierno).
    CLASSROOM_TZ = timezone(timedelta(hours=-5), "UTC-5")


def now() -> datetime:
    """Hora actual en el salón — no la del servidor donde corre esto."""
    return datetime.now(CLASSROOM_TZ)


def hour_of_day() -> float:
    """
    Hora del día como número decimal: 13.5 = 1:30 p.m.

    Es lo que consume la simulación de luz natural, que trabaja con una
    curva de sol entre SUNRISE_HOUR y SUNSET_HOUR.
    """
    n = now()
    return n.hour + n.minute / 60.0
