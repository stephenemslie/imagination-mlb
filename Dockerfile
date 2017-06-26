FROM python:3.6.1
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --disable-pip-version-check --src=/usr/local/src -r requirements.txt
RUN curl -L -o /usr/local/bin/jp https://github.com/jmespath/jp/releases/download/0.1.2/jp-linux-amd64 && chmod +x /usr/local/bin/jp
COPY . /app
ARG RELEASE_AUTH
RUN get-leaderboard.sh
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn"]
