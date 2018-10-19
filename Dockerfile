FROM python:3

WORKDIR /app
ADD . /app

RUN \
pip install --no-cache-dir -r /app/requirements.txt

CMD python3 bot.py