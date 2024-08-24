import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Family, Product, Sales
from datetime import datetime
import io

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_load_data_endpoint(db):
    csv_content = io.StringIO("Family,Product Name,Product ID,Price,2023-07\nElectronics,Smartwatch,1,199.99,30\n")
    response = client.post("/load-data/", files={"file": ("test.csv", csv_content.getvalue())})
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Data loaded successfully"}

def test_get_product(db):
    # First, add a product
    family = Family(name="Electronics")
    product = Product(id=1, name="Smartphone", price=699.99, family_id=1)
    db = TestingSessionLocal()
    db.add(family)
    db.add(product)
    db.commit()

    response = client.get("/product/1")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "data": {
            "id": 1,
            "name": "Smartphone",
            "price": 699.99,
            "family_id": 1
        }
    }

def test_update_product(db):
    # First, add a product
    family = Family(name="Electronics")
    product = Product(id=1, name="Smartphone", price=699.99, family_id=1)
    db = TestingSessionLocal()
    db.add(family)
    db.add(product)
    db.commit()

    response = client.put("/product/1?price=799.99")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Product updated successfully"}

    # Verify the update
    response = client.get("/product/1")
    assert response.json()["data"]["price"] == 799.99

def test_add_product_to_family(db):
    # First, add a family and a product
    family1 = Family(name="Electronics")
    family2 = Family(name="Home Appliances")
    product = Product(id=1, name="Smartphone", price=699.99, family_id=1)
    db = TestingSessionLocal()
    db.add(family1)
    db.add(family2)
    db.add(product)
    db.commit()

    response = client.post("/family/2/product/?product_id=1")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Product added to family successfully"}

    # Verify the update
    response = client.get("/product/1")
    assert response.json()["data"]["family_id"] == 2

def test_get_family(db):
    # First, add a family
    family = Family(name="Electronics")
    db = TestingSessionLocal()
    db.add(family)
    db.commit()

    response = client.get("/family/1")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "data": {
            "id": 1,
            "name": "Electronics"
        }
    }

def test_get_product_sales_last_year(db):
    # First, add a product and some sales
    family = Family(name="Electronics")
    product = Product(id=1, name="Smartphone", price=699.99, family_id=1)
    sale1 = Sales(product_id=1, date=datetime.now().date(), quantity=10)
    sale2 = Sales(product_id=1, date=datetime.now().date(), quantity=20)
    db = TestingSessionLocal()
    db.add(family)
    db.add(product)
    db.add(sale1)
    db.add(sale2)
    db.commit()

    response = client.get("/product/1/sales/last-year")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "total_sales": 30}