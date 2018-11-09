FROM python:3

WORKDIR /app
ADD /src /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD python3 bot.py