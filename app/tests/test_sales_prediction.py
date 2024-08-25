import pytest
from unittest.mock import MagicMock
import pandas as pd
import numpy as np
from datetime import date
from app.models import Sales, Product
from app.sales_prediction import SalesPredictor

@pytest.fixture
def mock_db():
    """Fixture to provide a mock database session."""
    db = MagicMock()
    
    # Mock sales data
    sales_data = [
        (Sales(id=1, product_id=1, date=date(2023, 1, 1), quantity=10), 100.0),
        (Sales(id=2, product_id=1, date=date(2023, 2, 1), quantity=20), 100.0),
        (Sales(id=3, product_id=2, date=date(2023, 1, 1), quantity=15), 200.0),
        (Sales(id=4, product_id=2, date=date(2023, 2, 1), quantity=25), 200.0)
    ]
    
    # Mock query to return sales data
    db.query.return_value.join.return_value.all.return_value = sales_data
    return db

def test_load_sales_data(mock_db):
    predictor = SalesPredictor(mock_db)
    df = predictor.load_sales_data()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'days_since_start' in df.columns
    assert 'revenue' in df.columns

def test_train_model_quantity(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()
    predictor.train_model('quantity')
    
    assert predictor.quantity_model is not None
    assert hasattr(predictor, 'X_test_quantity')
    assert hasattr(predictor, 'y_test_quantity')

def test_train_model_revenue(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()
    predictor.train_model('revenue')
    
    assert predictor.revenue_model is not None
    assert hasattr(predictor, 'X_test_revenue')
    assert hasattr(predictor, 'y_test_revenue')

def test_evaluate_model_quantity(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()
    predictor.train_model('quantity')
    
    mae, mse, rmse = predictor.evaluate_model('quantity')
    
    assert isinstance(mae, float)
    assert isinstance(mse, float)
    assert isinstance(rmse, float)
    assert mae >= 0
    assert mse >= 0
    assert rmse >= 0

def test_evaluate_model_revenue(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()
    predictor.train_model('revenue')
    
    mae, mse, rmse = predictor.evaluate_model('revenue')
    
    assert isinstance(mae, float)
    assert isinstance(mse, float)
    assert isinstance(rmse, float)
    assert mae >= 0
    assert mse >= 0
    assert rmse >= 0

def test_generate_prediction_report(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()
    predictor.train_model('quantity')
    predictor.train_model('revenue')
    
    report_df = predictor.generate_prediction_report()
    
    assert isinstance(report_df, pd.DataFrame)
    assert 'product_id' in report_df.columns
    assert 'actual_quantity' in report_df.columns
    assert 'predicted_quantity' in report_df.columns
    assert 'actual_revenue' in report_df.columns
    assert 'predicted_revenue' in report_df.columns
    assert 'quantity_error' in report_df.columns
    assert 'revenue_error' in report_df.columns

def test_run(mock_db, capsys):
    predictor = SalesPredictor(mock_db)
    predictor.run()
    
    captured = capsys.readouterr()
    assert "Quantity Model Evaluation Report:" in captured.out
    assert "Revenue Model Evaluation Report:" in captured.out
    assert "Prediction Report:" in captured.out