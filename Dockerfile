FROM python:3.12-alpine
RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR app/

COPY ./requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

LABEL authors="inncent"

CMD ["celery", "-A", "retail", "worker", "-l", "info"]