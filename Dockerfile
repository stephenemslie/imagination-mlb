FROM python:3.6.5
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --disable-pip-version-check --src=/usr/local/src -r requirements.txt
COPY . /app
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn"]
