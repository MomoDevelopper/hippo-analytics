"""
Modèle ORM pour les entraîneurs.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.cheval import Cheval


class Entraineur(Base):
    __tablename__ = "entraineurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prenom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    nationalite: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ecurie: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    ville: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    actif: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relations
    chevaux: Mapped[List["Cheval"]] = relationship("Cheval", back_populates="entraineur")

    def __repr__(self) -> str:
        return f"<Entraineur(id={self.id}, nom='{self.nom} {self.prenom}')>"
