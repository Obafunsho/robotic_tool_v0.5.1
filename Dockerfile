# Container for hosting the Robotic Programme Decision Tool (for example on
# Azure App Service UK South, AWS London, or a university server).
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MPLBACKEND=Agg
RUN python -m pytest -q
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
