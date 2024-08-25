from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, APIRouter
from sqlalchemy.orm import Session
from app import models, database
from app.crud import ProductManager
import shutil
from sqlalchemy.exc import IntegrityError
import os
import logging

app = FastAPI(
    title="Sales Data API",
    description="API for managing sales data, including products and their sales information.",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "404rex@gmail.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/load-data/", tags=["Data Loading"])
def load_data_endpoint(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    """
    Load data from a file into the database.

    Args:
        file (UploadFile): The file containing the data to be loaded.
        db (Session): The database session.

    Returns:
        dict: A message indicating the success of the operation.

    Raises:
        HTTPException: If there's a database integrity error or any unexpected error occurs.
    """
    file_location = f"/tmp/{file.filename}"
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        product_service = ProductManager(db)
        product_service.load_data(file_location)
        
        os.remove(file_location)
        return {"status": "success", "message": "Data loaded successfully"}

    except IntegrityError as e:
        logger.error(f"Database integrity error: {str(e)}")
        if 'duplicate key value' in str(e.orig):
            raise HTTPException(status_code=400, detail="Duplicate key error: The product ID already exists in the database.")
        raise HTTPException(status_code=500, detail="Database error occurred.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/product/{product_id}", tags=["Products"])
def get_product(product_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve a product by its ID.

    Args:
        product_id (int): The ID of the product to retrieve.
        db (Session): The database session.

    Returns:
        dict: The product details.

    Raises:
        HTTPException: If the product is not found.
    """
    product_service = ProductManager(db)
    product = product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "success", "data": product}


@router.put("/product/{product_id}", tags=["Products"])
def update_product(product_id: int, price: float, db: Session = Depends(database.get_db)):
    """
    Update a product's price.

    Args:
        product_id (int): The ID of the product to update.
        price (float): The new price for the product.
        db (Session): The database session.

    Returns:
        dict: A message indicating the success of the operation.

    Raises:
        HTTPException: If the product is not found.
    """
    product_service = ProductManager(db)
    product = product_service.update_product(product_id, price)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "success", "message": "Product updated successfully"}


@router.post("/family/{family_id}/product/", tags=["Families", "Products"])
def add_product_to_family(family_id: int, product_id: int, db: Session = Depends(database.get_db)):
    """
    Add a product to a family.

    Args:
        family_id (int): The ID of the family to add the product to.
        product_id (int): The ID of the product to add to the family.
        db (Session): The database session.

    Returns:
        dict: A message indicating the success of the operation.

    Raises:
        HTTPException: If either the family or the product is not found.
    """
    product_service = ProductManager(db)
    
    family = product_service.get_family(family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    product = product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.family_id = family.id
    db.commit()
    return {"status": "success", "message": "Product added to family successfully"}


@router.get("/family/{family_id}", tags=["Families"])
def get_family(family_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve family details by ID.

    Args:
        family_id (int): The ID of the family to retrieve.
        db (Session): The database session.

    Returns:
        dict: The family details.

    Raises:
        HTTPException: If the family is not found.
    """
    product_service = ProductManager(db)
    family = product_service.get_family(family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return {"status": "success", "data": family}
    

@router.get("/product/{product_id}/sales/last-year", tags=["Sales"])
def get_product_sales_last_year(product_id: int, db: Session = Depends(database.get_db)):
    """
    Get the total sales for a product in the last year.

    Args:
        product_id (int): The ID of the product to get sales for.
        db (Session): The database session.

    Returns:
        dict: The total sales for the product in the last year.
    """
    product_service = ProductManager(db)
    total_sales = product_service.get_product_sales_last_year(product_id)
    return {"status": "success", "total_sales": total_sales}

app.include_router(router)