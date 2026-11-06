"""
Modèle ORM pour les évaluations (notes calculées par partant et par course).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.partant import Partant
    from app.models.course import Course
    from app.models.cheval import Cheval


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    partant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partants.id"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    cheval_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chevaux.id"), nullable=False, index=True
    )

    # Notes détaillées (0 à 100)
    note_globale: Mapped[float] = mapped_column(Float, default=50.0)
    note_forme: Mapped[float] = mapped_column(Float, default=50.0)        # 5 dernières sorties
    note_distance: Mapped[float] = mapped_column(Float, default=50.0)     # affinité à la distance
    note_jockey: Mapped[float] = mapped_column(Float, default=50.0)       # performances du jockey
    note_entraineur: Mapped[float] = mapped_column(Float, default=50.0)   # performances de l'entraîneur
    note_regularite: Mapped[float] = mapped_column(Float, default=50.0)   # régularité des résultats
    note_cote: Mapped[float] = mapped_column(Float, default=50.0)         # analyse de la cote

    # Probabilités et classement
    probabilite_victoire: Mapped[float] = mapped_column(Float, default=0.0)
    probabilite_top3: Mapped[float] = mapped_column(Float, default=0.0)
    probabilite_top5: Mapped[float] = mapped_column(Float, default=0.0)
    rang_predit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Catégorie d'analyse
    # favori_stat, favori_cote, outsider_interessant, cheval_risque
    categorie: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relations
    partant: Mapped["Partant"] = relationship("Partant", back_populates="evaluation")

    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, partant_id={self.partant_id}, note={self.note_globale:.1f})>"
