"""Bitácora: deja constancia de cada alta, baja, modificación o anulación (requisito del enunciado:
«registrar todas las operaciones realizadas en una base de datos»).

`registrar` NO hace commit: la anotación viaja en la misma transacción que la operación. Si la operación
falla y se deshace, la anotación también se deshace; si se confirma, quedan juntas.

Nunca pongas contraseñas ni hashes en `detalle`.
"""
from sqlalchemy.orm import Session

from app.models.bitacora import Bitacora
from app.models.enumeraciones import AccionBitacora, EntidadBitacora


def registrar(
    db: Session,
    usuario_id: int,
    entidad: EntidadBitacora,
    entidad_id: int,
    accion: AccionBitacora,
    detalle: dict | None = None,
) -> None:
    db.add(Bitacora(usuario_id=usuario_id, entidad=entidad, entidad_id=entidad_id, accion=accion, detalle=detalle))
