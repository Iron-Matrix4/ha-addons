ARG BUILD_FROM
FROM python:3.11-slim

WORKDIR /app
COPY proxy.py .
RUN pip install --no-cache-dir flask requests

CMD ["python", "proxy.py"]
