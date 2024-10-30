FROM python:3.12

EXPOSE 81

WORKDIR /code

RUN pip install --no-cache-dir poetry==1.8.4

COPY ./pyproject.toml /code/pyproject.toml

RUN poetry install --no-cache

COPY ./app /code/app

CMD ["poetry", "run", "fastapi", "run", "app/main.py", "--port", "81"]