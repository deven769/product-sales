import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy.orm import Session
from typing import Tuple
from app.database import get_db
from app.models import Sales

class SalesPredictor:
    def __init__(self, db: Session):
        self.db = db
        self.df = None
        self.model = None
        self.X_test = None
        self.y_test = None

    def load_sales_data(self) -> pd.DataFrame:
        """
        Fetches sales data from the database and preprocesses it into a pandas DataFrame.
        """
        try:
            # Fetch sales data from the database
            sales_data = self.db.query(Sales).all()
            
            # Convert to pandas DataFrame
            df = pd.DataFrame([(sale.product_id, sale.date, sale.quantity) for sale in sales_data], 
                              columns=['product_id', 'date', 'quantity'])
            
            # Feature engineering: Convert date to numerical value (e.g., days since start)
            df['date'] = pd.to_datetime(df['date'])
            df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
            
            # Sort by product_id and date
            df = df.sort_values(by=['product_id', 'date'])
            
            self.df = df
            return df

        except Exception as e:
            print(f"Error loading sales data: {e}")
            raise

    def train_model(self) -> None:
        """
        Trains a linear regression model to predict sales.
        """
        try:
            if self.df is None:
                raise ValueError("Sales data not loaded.")
                
            # Features and target variable
            X = self.df[['days_since_start', 'product_id']]
            y = self.df['quantity']
            
            # Split the data into training and testing sets
            X_train, self.X_test, y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Initialize and train the model
            self.model = LinearRegression()
            self.model.fit(X_train, y_train)

        except Exception as e:
            print(f"Error training model: {e}")
            raise

    def evaluate_model(self) -> Tuple[float, float, float]:
        """
        Evaluates the performance of the trained model using the test dataset.
        """
        try:
            if self.model is None or self.X_test is None or self.y_test is None:
                raise ValueError("Model not trained or test data not available.")
                
            # Predict sales using the test set
            y_pred = self.model.predict(self.X_test)
            
            # Calculate evaluation metrics
            mae = mean_absolute_error(self.y_test, y_pred)
            mse = mean_squared_error(self.y_test, y_pred)
            rmse = np.sqrt(mse)
            
            return mae, mse, rmse

        except Exception as e:
            print(f"Error evaluating model: {e}")
            raise

    def run(self) -> None:
        """
        Orchestrates the loading of data, training of the model, and evaluation of the model.
        """
        try:
            # Load the database session
            db = next(get_db())
            
            # Initialize the predictor
            self.__init__(db)  # Reset instance with the new database session
            
            # Load sales data
            self.load_sales_data()
            
            # Train the model
            self.train_model()
            
            # Evaluate the model
            mae, mse, rmse = self.evaluate_model()
            
            # Print the evaluation report
            print("Model Evaluation Report:")
            print(f"Mean Absolute Error (MAE): {mae:.4f}")
            print(f"Mean Squared Error (MSE): {mse:.4f}")
            print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")

        except Exception as e:
            print(f"Error in main execution: {e}")
            raise

if __name__ == "__main__":
    predictor = SalesPredictor(next(get_db()))
    predictor.run()
