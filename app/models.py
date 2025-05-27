from datetime import date
from typing import List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey



class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

mechanic_ticket = Table(
    'mechanic_ticket',
    Base.metadata,
    Column('mechanic_id', Integer, ForeignKey('mechanics.id'), primary_key=True),
    Column('service_ticket_id', Integer, ForeignKey('service_tickets.id'), primary_key=True)
)

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(50), nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)

    service_tickets: Mapped[List['Service_Ticket']] = db.relationship(back_populates='customer')

class Service_Ticket(Base):
    __tablename__ = 'service_tickets'

    id: Mapped[int] = mapped_column(primary_key=True)

    VIN: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    service_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    service_desc: Mapped[str] = mapped_column(db.String(500), nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'), nullable=False)

    customer: Mapped[Customer] = db.relationship(back_populates='service_tickets')
    mechanics: Mapped[List['Mechanic']] = db.relationship(secondary=mechanic_ticket, back_populates='service_tickets')

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(50), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    service_tickets: Mapped[List['Service_Ticket']] = db.relationship(secondary=mechanic_ticket, back_populates='mechanics')
