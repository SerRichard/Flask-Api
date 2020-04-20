FROM python:3.7-alpine
WORKDIR /c02-api
COPY . /c02-api
RUN pip3 install -r requirements.txt
EXPOSE 80
CMD ["python", "c02_api.py"]
