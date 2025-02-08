FROM python:3.12
WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENV MY_ENV_VAR="value"
EXPOSE 27017