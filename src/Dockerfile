FROM python:3.12-alpine3.19

RUN apk add --update --no-cache nginx

# Install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the application
COPY ./ /app
WORKDIR /app
ENTRYPOINT ["/app/entrypoint.sh"]
