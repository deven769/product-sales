import pytest
from unittest.mock import MagicMock
import pandas as pd
from app.models import Sales
from app.sales_prediction import SalesPredictor

@pytest.fixture
def mock_db():
    """Fixture to provide a mock database session."""
    db = MagicMock()
    
    # Mock sales data
    sales_data = [
        Sales(product_id=1, date='2023-01-01', quantity=10),
        Sales(product_id=1, date='2023-02-01', quantity=20),
        Sales(product_id=2, date='2023-01-01', quantity=15),
        Sales(product_id=2, date='2023-02-01', quantity=25)
    ]
    
    # Mock query to return sales data
    db.query.return_value.all.return_value = sales_data
    return db

def test_load_sales_data(mock_db):
    predictor = SalesPredictor(mock_db)
    df = predictor.load_sales_data()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'days_since_start' in df.columns

def test_train_model(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()  # Load data into the instance
    predictor.train_model()
    
    assert predictor.model is not None
    assert hasattr(predictor, 'X_test')
    assert hasattr(predictor, 'y_test')

def test_evaluate_model(mock_db):
    predictor = SalesPredictor(mock_db)
    predictor.load_sales_data()
    predictor.train_model()
    
    mae, mse, rmse = predictor.evaluate_model()
    
    assert isinstance(mae, float)
    assert isinstance(mse, float)
    assert isinstance(rmse, float)
    assert mae >= 0
    assert mse >= 0
    assert rmse >= 0

def test_run(mock_db, capsys):
    predictor = SalesPredictor(mock_db)
    predictor.run()
    
    captured = capsys.readouterr()
    assert "Model Evaluation Report:" in captured.out
