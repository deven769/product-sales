from sqlalchemy.orm import Session
from app import models
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ProductManager:
    def __init__(self, db: Session):
        self.db = db

    def read_csv_with_encoding(self, file_path: str, encodings: list, delimiters: list) -> pd.DataFrame:
        """
        Try to read the CSV file with a list of encodings and delimiters.
        """
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    return pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, on_bad_lines='warn')
                except (UnicodeDecodeError, pd.errors.ParserError) as e:
                    logger.warning(f"Parsing error with encoding {encoding} and delimiter {delimiter}: {e}")
        raise Exception("Unable to read the file with provided encodings and delimiters.")

    def load_data(self, file_path: str):
        encodings = ['utf-8', 'latin1', 'ISO-8859-1']
        delimiters = [',', ';', '\t']
        
        # Read the CSV file into a DataFrame
        df = self.read_csv_with_encoding(file_path, encodings, delimiters)
        
        for _, row in df.iterrows():
            family_name = row.get('Family')
            if not family_name:
                continue

            # Get or create the family
            family = self.db.query(models.Family).filter(models.Family.name == family_name).first()
            if not family:
                family = models.Family(name=family_name)
                self.db.add(family)
                self.db.commit()
                self.db.refresh(family)
            
            # Check if the product already exists
            product_id = row.get('Product ID')
            existing_product = self.db.query(models.Product).filter(models.Product.id == product_id).first()
            
            if existing_product:
                logger.info(f"Product with ID {product_id} already exists, skipping.")
                continue  # Skip to the next product if it already exists

            # Create the product if it doesn't exist
            product = models.Product(
                name=row.get('Product Name'),
                id=product_id,
                price=row.get('Price'),
                family_id=family.id
            )
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            
            # Add sales data
            for col in df.columns[4:]:
                try:
                    date = datetime.strptime(col, '%Y-%m')
                    quantity = row.get(col, 0)
                    # Ensure quantity is an integer
                    quantity = int(quantity) if quantity else 0
                    
                    sales = models.Sales(
                        product_id=product.id,
                        date=date,
                        quantity=quantity
                    )
                    self.db.add(sales)
                except ValueError as e:
                    logger.warning(f"Date parsing error: {e}")
                    
        # Commit all changes to the database
        self.db.commit()

    def get_product(self, product_id: int):
        return self.db.query(models.Product).filter(models.Product.id == product_id).first()

    def update_product(self, product_id: int, price: float):
        product = self.get_product(product_id)
        if product:
            product.price = price
            self.db.commit()
            return product
        return None

    def get_family(self, family_id: int):
        return self.db.query(models.Family).filter(models.Family.id == family_id).first()

    def get_product_sales_last_year(self, product_id: int):
        one_year_ago = datetime.now().replace(year=datetime.now().year - 1)
        sales = self.db.query(models.Sales).filter(
            models.Sales.product_id == product_id,
            models.Sales.date >= one_year_ago
        ).all()
        return sum(sale.quantity for sale in sales)
