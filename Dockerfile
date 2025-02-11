FROM python:3.12-alpine
RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR app/

COPY ./requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR app/

EXPOSE 8000

RUN ["python3", "manage.py", "migrate"]

LABEL authors="inncent"

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["celery", "-A", "retail", "worker", "-l", "info", "-c"]
