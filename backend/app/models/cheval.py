"""
Modèle ORM pour les chevaux.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.entraineur import Entraineur
    from app.models.partant import Partant
    from app.models.performance import Performance


class Cheval(Base):
    __tablename__ = "chevaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # M=Mâle, F=Femelle, H=Hongre, P=Pouliche
    sexe: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    robe: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origine: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    proprietaire: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    naisseur: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    pays_naissance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entraineur_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("entraineurs.id"), nullable=True
    )
    actif: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relations
    entraineur: Mapped[Optional["Entraineur"]] = relationship(
        "Entraineur", back_populates="chevaux"
    )
    partants: Mapped[List["Partant"]] = relationship("Partant", back_populates="cheval")
    performances: Mapped[List["Performance"]] = relationship(
        "Performance", back_populates="cheval"
    )

    def __repr__(self) -> str:
        return f"<Cheval(id={self.id}, nom='{self.nom}', age={self.age})>"
