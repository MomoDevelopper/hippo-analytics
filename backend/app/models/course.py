"""
Modèle ORM pour les courses hippiques.
"""
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Date, Float, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum

if TYPE_CHECKING:
    from app.models.partant import Partant
    from app.models.pronostic import Pronostic
    from app.models.arrivee import Arrivee


class StatutCourse(str, enum.Enum):
    PROGRAMMEE = "programmée"
    EN_COURS = "en_cours"
    TERMINEE = "terminée"
    ANNULEE = "annulée"


class TypePiste(str, enum.Enum):
    HERBE = "herbe"
    SABLE = "sable"
    SYNTHETIQUE = "synthétique"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date_course: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reunion: Mapped[str] = mapped_column(String(10), nullable=False)       # R1, R2...
    numero_course: Mapped[int] = mapped_column(Integer, nullable=False)    # C1, C2...
    hippodrome: Mapped[str] = mapped_column(String(150), nullable=False)
    distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # en mètres
    type_piste: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    conditions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    nombre_partants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allocation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # dotation €/FCFA
    statut: Mapped[str] = mapped_column(
        String(20), default=StatutCourse.PROGRAMMEE.value, nullable=False
    )
    programme_source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relations
    partants: Mapped[List["Partant"]] = relationship("Partant", back_populates="course")
    pronostics: Mapped[List["Pronostic"]] = relationship("Pronostic", back_populates="course")
    arrivee: Mapped[Optional["Arrivee"]] = relationship(
        "Arrivee", back_populates="course", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, date={self.date_course}, R{self.reunion}C{self.numero_course})>"
