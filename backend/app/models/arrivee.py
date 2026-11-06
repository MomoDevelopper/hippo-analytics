"""
Modèle ORM pour les arrivées officielles (résultats des courses).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, DateTime, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON
from app.database import Base

# Utilise JSON standard (compatible SQLite + PostgreSQL)
JSONB = JSON

if TYPE_CHECKING:
    from app.models.course import Course


class Arrivee(Base):
    __tablename__ = "arrivees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Une seule arrivée par course
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), unique=True, nullable=False, index=True
    )
    # Classement officiel : liste ordonnée de cheval_ids [1er, 2ème, 3ème, 4ème, 5ème, ...]
    classement_officiel: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Détails : [{"cheval_id": x, "place": 1, "temps": "1'42''3", "ecart": "...", "gains": 0}, ...]
    classement_detaille: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Source : "officielle" (résultat confirmé) ou "provisoire"
    source: Mapped[str] = mapped_column(String(20), default="provisoire")
    date_enregistrement: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    saisi_par: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    course: Mapped["Course"] = relationship("Course", back_populates="arrivee")

    def __repr__(self) -> str:
        return f"<Arrivee(id={self.id}, course_id={self.course_id}, source='{self.source}')>"
