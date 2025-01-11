FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./templates /code/templates
COPY ./static /code/app/static
COPY ./routers /code/app/routers
COPY ./models.py /code/app/models.py
COPY ./database.py /code/app/database.py


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./ /code/app