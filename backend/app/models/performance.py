"""
Modèle ORM pour les performances historiques des chevaux.
"""
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Date, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.cheval import Cheval
    from app.models.course import Course
    from app.models.jockey import Jockey


class Performance(Base):
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cheval_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chevaux.id"), nullable=False, index=True
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=True, index=True
    )
    jockey_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jockeys.id"), nullable=True
    )
    date_course: Mapped[date] = mapped_column(Date, nullable=False)
    hippodrome: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    type_piste: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    place_officielle: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    partants_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temps: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # ex: "1'42''3"
    ecart: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # ex: "3 têtes"
    cote_depart: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gains: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    numero_partant: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    poids: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    cheval: Mapped["Cheval"] = relationship("Cheval", back_populates="performances")
    jockey: Mapped[Optional["Jockey"]] = relationship("Jockey", back_populates="performances")

    def __repr__(self) -> str:
        return f"<Performance(id={self.id}, cheval_id={self.cheval_id}, place={self.place_officielle})>"
