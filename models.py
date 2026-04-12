from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel

class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String, default="free")
    discount = Column(Float, default=0)
    note = Column(String, nullable=True)  # 🔥 هذا المهم

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    position = Column(Integer, default=0)

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)

    category_id = Column(Integer, ForeignKey("categories.id"))
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)  # 🔥 جديد
    section = Column(String)

    category = relationship("Category")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"))
    status = Column(String, default="pending")

    table = relationship("Table")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer)

    order = relationship("Order")
    item = relationship("MenuItem")




class GroupOrder(BaseModel):
    id: int
    position: int



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # admin / waiter