import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from typing import Tuple, List
from app.database import get_db
from app.models import Sales, Product

class SalesPredictor:
    def __init__(self, db: Session):
        self.db = db
        self.df = None
        self.quantity_model = None
        self.revenue_model = None
        self.X_test_quantity = None
        self.y_test_quantity = None
        self.X_test_revenue = None
        self.y_test_revenue = None

    def load_sales_data(self) -> pd.DataFrame:
        """
        Fetches sales data from the database and preprocesses it into a pandas DataFrame.
        """
        try:
            # Fetch sales data along with product price
            sales_data = self.db.query(Sales, Product.price).join(Product, Sales.product_id == Product.id).all()
            
            # Convert to pandas DataFrame
            df = pd.DataFrame([(sale[0].product_id, sale[0].date, sale[0].quantity, sale[1]) 
                               for sale in sales_data], 
                              columns=['product_id', 'date', 'quantity', 'price'])
            
            # Feature engineering: Convert date to numerical value (e.g., days since start)
            df['date'] = pd.to_datetime(df['date'])
            df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
            
            # Calculate revenue as quantity * price
            df['revenue'] = df['quantity'] * df['price']
            
            # Sort by product_id and date
            df = df.sort_values(by=['product_id', 'date'])
            
            self.df = df
            return df

        except Exception as e:
            print(f"Error loading sales data: {e}")
            raise

    def train_model(self, target: str) -> None:
        """
        Trains a linear regression model to predict either quantity or revenue.
        """
        try:
            if self.df is None:
                raise ValueError("Sales data not loaded.")
            
            # Features
            X = self.df[['days_since_start', 'product_id']]
            y = self.df[target]
            
            # Split the data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Initialize and train the model
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            if target == 'quantity':
                self.quantity_model = model
                self.X_test_quantity = X_test
                self.y_test_quantity = y_test
            elif target == 'revenue':
                self.revenue_model = model
                self.X_test_revenue = X_test
                self.y_test_revenue = y_test

        except Exception as e:
            print(f"Error training {target} model: {e}")
            raise

    def evaluate_model(self, target: str) -> Tuple[float, float, float]:
        """
        Evaluates the performance of the trained model using the test dataset.
        """
        try:
            if target == 'quantity':
                model = self.quantity_model
                X_test = self.X_test_quantity
                y_test = self.y_test_quantity
            elif target == 'revenue':
                model = self.revenue_model
                X_test = self.X_test_revenue
                y_test = self.y_test_revenue
            else:
                raise ValueError("Invalid target specified. Use 'quantity' or 'revenue'.")

            if model is None or X_test is None or y_test is None:
                raise ValueError(f"{target.capitalize()} model not trained or test data not available.")
                
            # Predict using the test set
            y_pred = model.predict(X_test)
            
            # Calculate evaluation metrics
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            return mae, mse, rmse

        except Exception as e:
            print(f"Error evaluating {target} model: {e}")
            raise

    def generate_prediction_report(self) -> pd.DataFrame:
        """
        Generates a prediction report comparing the actual and predicted values for both quantity and revenue.
        """
        try:
            if self.quantity_model is None or self.revenue_model is None:
                raise ValueError("Models are not trained.")

            # Predict quantity and revenue
            y_pred_quantity = self.quantity_model.predict(self.X_test_quantity)
            y_pred_revenue = self.revenue_model.predict(self.X_test_revenue)
            
            # Compile the actual vs predicted DataFrame
            report_data = {
                'product_id': self.X_test_quantity['product_id'].values,
                'actual_quantity': self.y_test_quantity,
                'predicted_quantity': y_pred_quantity,
                'actual_revenue': self.y_test_revenue,
                'predicted_revenue': y_pred_revenue
            }
            report_df = pd.DataFrame(report_data)

            # Generate error metrics for additional insight
            report_df['quantity_error'] = report_df['actual_quantity'] - report_df['predicted_quantity']
            report_df['revenue_error'] = report_df['actual_revenue'] - report_df['predicted_revenue']
            report_df.to_csv('output/prediction_report.csv', index=False)
            return report_df

        except Exception as e:
            print(f"Error generating prediction report: {e}")
            raise

    def run(self) -> None:
        """
        Orchestrates the loading of data, training of the models, evaluation of the models, and generation of the prediction report.
        """
        try:
            # Load sales data
            self.load_sales_data()
            
            # Train the quantity model
            self.train_model(target='quantity')
            
            # Train the revenue model
            self.train_model(target='revenue')
            
            # Evaluate the quantity model
            quantity_mae, quantity_mse, quantity_rmse = self.evaluate_model(target='quantity')
            print("Quantity Model Evaluation Report:")
            print(f"Mean Absolute Error (MAE): {quantity_mae:.4f}")
            print(f"Mean Squared Error (MSE): {quantity_mse:.4f}")
            print(f"Root Mean Squared Error (RMSE): {quantity_rmse:.4f}")
            
            # Evaluate the revenue model
            revenue_mae, revenue_mse, revenue_rmse = self.evaluate_model(target='revenue')
            print("\nRevenue Model Evaluation Report:")
            print(f"Mean Absolute Error (MAE): {revenue_mae:.4f}")
            print(f"Mean Squared Error (MSE): {revenue_mse:.4f}")
            print(f"Root Mean Squared Error (RMSE): {revenue_rmse:.4f}")
            
            # Generate and display prediction report
            report_df = self.generate_prediction_report()
            print("\nPrediction Report:")
            print(report_df.head())  # Display the first few rows of the report

        except Exception as e:
            print(f"Error in main execution: {e}")
            raise

if __name__ == "__main__":
    predictor = SalesPredictor(next(get_db()))
    predictor.run()