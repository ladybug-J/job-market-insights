FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY ./streamlit-app app/streamlit-app
COPY ./etl app/etl
EXPOSE 8501
ENTRYPOINT ["streamlit", "run"]
CMD ["streamlit-app/app.py"]