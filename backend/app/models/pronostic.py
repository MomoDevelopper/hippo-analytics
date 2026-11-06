"""
Modèle ORM pour les pronostics (hypothèses générées avant le départ).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, Text, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON
from app.database import Base

# Utilise JSON standard (compatible SQLite + PostgreSQL)
JSONB = JSON

if TYPE_CHECKING:
    from app.models.course import Course


class Pronostic(Base):
    __tablename__ = "pronostics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    date_generation: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Top 5 prédit : liste ordonnée de 5 IDs de chevaux
    top5_predit: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Ordre prédit complet (liste de cheval_ids dans l'ordre estimé)
    ordre_predit: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Probabilités : {"cheval_id": probabilite_victoire, ...}
    probabilites: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Top hypothèses : [{"ordre": [id1,id2,id3,id4,id5], "probabilite": 0.0085}, ...]
    top_hypotheses: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    methode_utilisee: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version_modele: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Verrouillé = plus modifiable après le départ (intégrité des données)
    verrouille: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    course: Mapped["Course"] = relationship("Course", back_populates="pronostics")

    def __repr__(self) -> str:
        return f"<Pronostic(id={self.id}, course_id={self.course_id}, verrouille={self.verrouille})>"
