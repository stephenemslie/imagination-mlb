FROM python:3.6.1
WORKDIR /app
RUN mkdir -p /app/bin && curl -o /app/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --disable-pip-version-check --src=/usr/local/src -r requirements.txt
COPY . /app
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn"]
