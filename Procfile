web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker application:application --bind 0.0.0.0:8000
worker: python -m app.tasks.sqs_worker