from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

class Family(Base):
    __tablename__ = 'families'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Relationship to Product
    products = relationship("Product", order_by="Product.id", back_populates="family")


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    family_id = Column(Integer, ForeignKey('families.id'), nullable=False)

    # Relationships
    family = relationship("Family", back_populates="products")
    sales = relationship("Sales", back_populates="product")


class Sales(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relationship to Product
    product = relationship("Product", back_populates="sales")
