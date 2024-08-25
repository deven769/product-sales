# Product Sales API

This project is a FastAPI web server that handles product sales data for a store, interacting with a PostgreSQL database.

## Installation

1. Clone the repository.
2. Make environment
   ```bash
   python -m venv env_name
   ```
3. Activate environment
4. Install dependencies:
   ```bash
   pip install -r requirements.txt 
   ```
5. Set database: 
   - Change line 63 in alembic.ini with your database credentials
   - Update .env for DATABASE_URL with your database credentials

6. Run server : navigate to project dir (cd sales)
```bash
   uvicorn app.main:app --reload
```
7. Access api at: http://127.0.0.1:8000/docs

## Options

8. Command for database migration and migrate
   <!-- alembic init alembic -->
   - Migrations: alembic revision --autogenerate -m "Initial migration"
   - Migrate: alembic upgrade head


## For Optional Task : Machine Learning

1. Navigate project dir and run sales_prediction.py script file
   ```bash 
   python -m app.sales_prediction
   ```

Note: Sales prediction load data from DATABASE