#lightweight Python image
FROM python:3.10-slim

#directory inside the container
WORKDIR /app

#Copy requirements file into the container
COPY requirements.txt .

#Install the Python packages
RUN pip install --no-cache-dir -r requirements.txt

#Copy rest of project files into the container
COPY . .

#Expose the port that Streamlit uses
EXPOSE 8501

#Tell Docker to run when the container starts
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]