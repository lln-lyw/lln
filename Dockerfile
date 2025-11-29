FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install flask paramiko
EXPOSE 5000
CMD ["python", "app.py"]
