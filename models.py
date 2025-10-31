import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# 🏷️ Category
class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(255))

    products = relationship("Product", back_populates="category")

class Brand(Base):
    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(255))

    products = relationship("Product", back_populates="brand")


# 📦 Product
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    stock_qnt = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    transactions = relationship("Transaction", back_populates="product")


# 🏬 Point of Sale
class POS(Base):
    __tablename__ = "pos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    region = Column(String(100), nullable=False)

    transactions = relationship("Transaction", back_populates="pos")


# 💰 Transaction
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    pos_id = Column(UUID(as_uuid=True), ForeignKey("pos.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    type = Column(String(16), default="sale")
    date = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="transactions")
    pos = relationship("POS", back_populates="transactions")
