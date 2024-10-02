FROM python:3.10
WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
EXPOSE 80
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:80", "app:app"]