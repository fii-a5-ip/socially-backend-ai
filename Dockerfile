
FROM python:3.11

WORKDIR /app_py_ai 

# dacă nu mere încearcă "COPY api.py ." și "COPY requirements.txt"     SAU       "ADD . ."
COPY requirements.txt .

# dacă nu mere, încearcă ”flask httpx orjson python-dotenv requests” înloc de ” -r requirements.txt”
RUN pip install -r requirements.txt


# dacă nu mere încearcă sa adaugi "COPY . .” sau "ADD . ."

COPY . .

#Nu cred ca este nevoie dar nici nu cred ca strica
EXPOSE 5000

CMD ["python", "-m", "api.api"]
