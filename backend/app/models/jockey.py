"""
Modèle ORM pour les jockeys.
"""
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.partant import Partant
    from app.models.performance import Performance


class Jockey(Base):
    __tablename__ = "jockeys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prenom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    nationalite: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date_naissance: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    licence_depuis: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    poids_reference: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # en kg
    actif: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relations
    partants: Mapped[List["Partant"]] = relationship("Partant", back_populates="jockey")
    performances: Mapped[List["Performance"]] = relationship(
        "Performance", back_populates="jockey"
    )

    def __repr__(self) -> str:
        return f"<Jockey(id={self.id}, nom='{self.nom} {self.prenom}')>"
