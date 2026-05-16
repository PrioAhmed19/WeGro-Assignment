# Agriculture Analytics FastAPI

FastAPI assessment project for serving agriculture database reports from MySQL using SQLAlchemy, PyMySQL, and pandas.

## What It Builds

The API connects to the pre-populated `agriculture_db`, loads `vw_harvest_full`, applies validated query filters, and returns 8 report endpoints:

- `GET /farms/summary`
- `GET /farms/{farm_id}/performance`
- `GET /farms/top`
- `GET /farms/loss-analysis`
- `GET /crops/yield-efficiency`
- `GET /crops/seasonal-trend`
- `GET /markets/price-comparison`
- `GET /crops/quality-breakdown`

Interactive docs are available at `http://localhost:8000/docs`.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a local `.env` file from `.env.example` and fill in the database credentials:

```bash
copy .env.example .env
```

Required environment variables:

```env
HOST=your_mysql_host
PORT=3306
DB=agriculture_db
USER=your_mysql_user
PASSWORD=your_mysql_password
```

## Run

From the project root:

```bash
cd E:\WEgro
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Example report calls:

```bash
curl "http://localhost:8000/farms/summary?region=Dhaka&year=2023"
curl "http://localhost:8000/farms/top?metric=profit&limit=5"
curl "http://localhost:8000/crops/yield-efficiency?crop_category=Cereal&year=2023"
curl "http://localhost:8000/markets/price-comparison?market_type=Export&price_tier=Premium"
```

## Docker

```bash
docker build -t agriculture-api .
docker run --env-file .env -p 8000:8000 agriculture-api
```

## Filter Validation

Invalid filter values return HTTP 422 with a clear message. Accepted values follow the PRD:

- `region`: Dhaka, Chittagong, Sylhet, Rajshahi, Khulna, Rangpur, Barisal, Mymensingh
- `farm_type`: Small, Medium, Large, Commercial
- `crop_category`: Cereal, Vegetable, Fruit, Pulse, Oilseed, Cash Crop, Spice
- `season`: Spring, Summer, Autumn, Winter
- `market_type`: Local, Wholesale, Export, Retail, Government Procurement
- `price_tier`: Low, Medium, High, Premium
- `quality_grade`: A, B, C, D
- `pesticide_residue`: None, Trace, Low, High
- `water_requirement`: Low, Medium, High
- `year`: 2022, 2023, 2024
- `quarter`: 1, 2, 3, 4
- `metric`: profit, revenue, yield
