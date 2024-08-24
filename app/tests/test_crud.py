import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.crud import ProductManager
from app.models import Family, Product, Sales
from datetime import datetime, timedelta
import pandas as pd
import tempfile
import os
import io

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def product_manager(db):
    return ProductManager(db)

def test_read_csv_with_encoding(product_manager):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp.write("Family,Product Name,Product ID,Price,2023-07\nElectronics,Smartwatch,1,199.99,30\n")
        tmp_path = tmp.name

    df = product_manager.read_csv_with_encoding(tmp_path, ['utf-8'], [','])
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 5)
    assert df.iloc[0]['Family'] == 'Electronics'

    os.unlink(tmp_path)

def test_load_data(product_manager, db):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp.write("Family,Product Name,Product ID,Price,2023-07\nElectronics,Smartwatch,1,199.99,30\n")
        tmp_path = tmp.name

    product_manager.load_data(tmp_path)

    family = db.query(Family).first()
    assert family.name == 'Electronics'

    product = db.query(Product).first()
    assert product.name == 'Smartwatch'
    assert product.id == 1
    assert product.price == 199.99

    sales = db.query(Sales).first()
    assert sales.quantity == 30
    assert sales.date == datetime(2023, 7, 1).date()

    os.unlink(tmp_path)

def test_load_data_existing_family(product_manager, db):
    # Add an existing family
    family = Family(name='Electronics')
    db.add(family)
    db.commit()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp.write("Family,Product Name,Product ID,Price,2023-07\nElectronics,Smartphone,2,299.99,20\n")
        tmp_path = tmp.name

    product_manager.load_data(tmp_path)

    families = db.query(Family).all()
    assert len(families) == 1  # Should not create a duplicate family

    product = db.query(Product).first()
    assert product.name == 'Smartphone'
    assert product.id == 2
    assert product.price == 299.99

    os.unlink(tmp_path)

def test_get_product(product_manager, db):
    family = Family(name='Electronics')
    db.add(family)
    db.commit()

    product = Product(id=1, name='Smartphone', price=699.99, family_id=family.id)
    db.add(product)
    db.commit()

    retrieved_product = product_manager.get_product(1)
    assert retrieved_product.id == 1
    assert retrieved_product.name == 'Smartphone'
    assert retrieved_product.price == 699.99

def test_get_nonexistent_product(product_manager):
    assert product_manager.get_product(999) is None

def test_update_product(product_manager, db):
    family = Family(name='Electronics')
    db.add(family)
    db.commit()

    product = Product(id=1, name='Smartphone', price=699.99, family_id=family.id)
    db.add(product)
    db.commit()

    updated_product = product_manager.update_product(1, 799.99)
    assert updated_product.price == 799.99

    retrieved_product = product_manager.get_product(1)
    assert retrieved_product.price == 799.99

def test_update_nonexistent_product(product_manager):
    assert product_manager.update_product(999, 99.99) is None

def test_get_family(product_manager, db):
    family = Family(name='Electronics')
    db.add(family)
    db.commit()

    retrieved_family = product_manager.get_family(1)
    assert retrieved_family.id == 1
    assert retrieved_family.name == 'Electronics'

def test_get_nonexistent_family(product_manager):
    assert product_manager.get_family(999) is None

def test_get_product_sales_last_year(product_manager, db):
    family = Family(name='Electronics')
    db.add(family)
    db.commit()

    product = Product(id=1, name='Smartphone', price=699.99, family_id=family.id)
    db.add(product)
    db.commit()

    now = datetime.now()
    one_year_ago = now - timedelta(days=365)
    two_years_ago = now - timedelta(days=730)

    sales1 = Sales(product_id=1, date=now.date(), quantity=10)
    sales2 = Sales(product_id=1, date=one_year_ago.date(), quantity=20)
    sales3 = Sales(product_id=1, date=two_years_ago.date(), quantity=30)
    db.add_all([sales1, sales2, sales3])
    db.commit()

    total_sales = product_manager.get_product_sales_last_year(1)
    assert total_sales == 30  # 10 + 20

def test_get_product_sales_last_year_no_sales(product_manager, db):
    family = Family(name='Electronics')
    db.add(family)
    db.commit()

    product = Product(id=1, name='Smartphone', price=699.99, family_id=family.id)
    db.add(product)
    db.commit()

    total_sales = product_manager.get_product_sales_last_year(1)
    assert total_sales == 0

def test_get_product_sales_last_year_nonexistent_product(product_manager):
    total_sales = product_manager.get_product_sales_last_year(999)
    assert total_sales == 0