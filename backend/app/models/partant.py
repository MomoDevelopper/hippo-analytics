"""
Modèle ORM pour les partants (chevaux engagés dans une course).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Float, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.cheval import Cheval
    from app.models.jockey import Jockey
    from app.models.evaluation import Evaluation


class Partant(Base):
    __tablename__ = "partants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    cheval_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chevaux.id"), nullable=False, index=True
    )
    jockey_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jockeys.id"), nullable=True
    )
    numero_partant: Mapped[int] = mapped_column(Integer, nullable=False)
    poids: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # en kg
    handicap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Musique = historique des performances (ex: "1a3h5D2p")
    musique: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cote_depart: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    non_partant: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relations
    course: Mapped["Course"] = relationship("Course", back_populates="partants")
    cheval: Mapped["Cheval"] = relationship("Cheval", back_populates="partants")
    jockey: Mapped[Optional["Jockey"]] = relationship("Jockey", back_populates="partants")
    evaluation: Mapped[Optional["Evaluation"]] = relationship(
        "Evaluation", back_populates="partant", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Partant(id={self.id}, numero={self.numero_partant}, course_id={self.course_id})>"
