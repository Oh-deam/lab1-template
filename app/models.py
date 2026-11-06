from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    work: Mapped[str | None] = mapped_column(String, nullable=True)