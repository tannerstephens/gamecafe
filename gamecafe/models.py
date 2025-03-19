from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import pbkdf2_hmac
from math import ceil
from os import urandom
from typing import Optional, Self

from sqlalchemy import Column, ForeignKey, Index, Table, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import db


class IdModel(db.Base):
    __abstract__ = True

    serializable: list[str] = ["id"]

    id: Mapped[int] = mapped_column(primary_key=True)

    @dataclass
    class Page[T]:
        items: list[T]
        page_count: int
        previous_page: Optional[int]
        next_page: Optional[int]
        current_page: int

        def serialize(self):
            return {
                "items": self.items,
                "page_count": self.page_count,
                "next_page": self.next_page,
                "previous_page": self.previous_page,
                "current_page": self.current_page,
            }

    @classmethod
    def all(cls):
        stmt = cls.select()

        return db.session.scalars(stmt).all()

    @classmethod
    def select(cls):
        return select(cls)

    @classmethod
    def count(cls) -> int:
        stmt = select(func.count(cls.id))
        res = db.session.execute(stmt).one()

        return res[0]

    @classmethod
    def paginate(cls, page: int, per_page: int) -> Page[Self]:
        stmt = cls.select().order_by(cls.id).offset((page - 1) * per_page).limit(per_page)

        items = db.session.scalars(stmt).all()

        item_count = cls.count()
        page_count = ceil(item_count / per_page)

        return cls.Page(
            items,
            page_count,
            page - 1 if page > 1 else None,
            page + 1 if page < page_count else None,
            page,
        )

    def serialize(self):
        return {key: getattr(self, key) for key in self.serializable}

    def save(self, commit=True):
        db.session.add(self)

        if commit:
            db.session.commit()

        return self

    def delete(self, commit=True):
        db.session.delete(self)

        if commit:
            db.session.commit()

    @classmethod
    def get_by_id(cls, oid: int):
        return db.session.get(cls, oid)


class BggItem(IdModel):
    __abstract__ = True

    bgg_id: Mapped[int] = mapped_column(unique=True)

    def __init__(self, bgg_id: int):
        self.bgg_id = bgg_id

    @classmethod
    def get_by_bgg_id(cls, bgg_id: int):
        stmt = cls.select().where(cls.bgg_id == bgg_id)

        return db.session.scalar(stmt)


publisher_game_table = Table(
    "publisher_game_table",
    db.Base.metadata,
    Column("game_id", ForeignKey("games.id"), primary_key=True),
    Column("publisher_id", ForeignKey("publishers.id"), primary_key=True),
)

game_tag_table = Table(
    "game_tag_table",
    db.Base.metadata,
    Column("game_id", ForeignKey("games.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Publisher(BggItem):
    __tablename__ = "publishers"

    name: Mapped[str]
    games: Mapped[list["Game"]] = relationship(
        secondary=publisher_game_table, back_populates="publishers"
    )

    def __init__(self, bgg_id: int, name: str):
        super().__init__(bgg_id)

        self.name = name


class Tag(BggItem):
    __tablename__ = "tags"

    class Type(Enum):
        CATEGORY = "category"
        MECHANIC = "mechanic"

        def __str__(self):
            return self.value.capitalize()

        def serialize(self):
            return str(self)

    name: Mapped[str]
    type: Mapped[Type]

    games: Mapped[list["Game"]] = relationship(secondary=game_tag_table, back_populates="tags")

    UniqueConstraint("bgg_id", "type", name="uq_bgg_id_type")

    def __init__(self, bgg_id, name: str, type: Type):
        super().__init__(bgg_id)

        self.name = name
        self.type = type


class Game(BggItem):
    __tablename__ = "games"

    name: Mapped[str]
    publishers: Mapped[list[Publisher]] = relationship(
        secondary=publisher_game_table, back_populates="games"
    )
    image_path: Mapped[Optional[str]]
    location: Mapped[Optional[str]]

    last_updated: Mapped[datetime] = mapped_column(server_default=func.now())
    tags: Mapped[list[Tag]] = relationship(secondary=game_tag_table, back_populates="games")

    def __init__(self, bgg_id: int, name: str, image_path: str | None):
        super().__init__(bgg_id)

        self.name = name
        self.image_path = image_path


class User(IdModel):
    class Role(Enum):
        USER = "user"
        EDITOR = "editor"
        ADMIN = "admin"

        def __str__(self):
            return self.value.capitalize()

        def serialize(self):
            return str(self)

    class PasswordException(Exception):
        pass

    __tablename__ = "users"

    def _set_password(self, password: str):
        if not self.validate_password(password):
            raise self.PasswordException()

        self.password_hash = self.hash_password(password)

    serializable = ["username", "email", "role"]

    username: Mapped[str]
    email: Mapped[str]
    password_hash: Mapped[str]

    role: Mapped[Role] = mapped_column(nullable=False, default=Role.USER)

    password = property(fset=_set_password)

    def __init__(self, email: str, username: str, password: str, role: Role = None):
        role = role or self.Role.USER

        self.email = email
        self.username = username
        self._set_password(password)
        self.role = role

    @classmethod
    def validate_password(cls, password: str):
        return len(password) >= 8

    def hash_password(self, password: str, salt: str | bytes | None = None):
        if salt is None:
            salt = urandom(32)
        elif isinstance(salt, str):
            salt = bytes.fromhex(salt)

        key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + "|" + key.hex()

    def check_password(self, password: str):
        salt = self.password_hash.split("|")[0]

        return self.hash_password(password, salt) == self.password_hash

    @classmethod
    def get_by_username(cls, username: str):
        stmt = cls.select().where(cls.username == username.lower())

        return db.session.scalar(stmt)

    @classmethod
    def get_by_email(cls, email: str):
        stmt = cls.select().where(cls.email == email.lower())

        return db.session.scalar(stmt)

    def __repr__(self):
        return f"<User: {self.username}>"


user_username_index = Index("user_username_idx", func.lower(User.username), unique=True)
user_email_index = Index("user_email_idx", func.lower(User.email), unique=True)
