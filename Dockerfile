
FROM python:3.14

WORKDIR /app_py_ai 

# dacă nu mere încearcă "COPY api.py ." și "COPY requirements.txt"     SAU       "ADD . ."
COPY requirements.txt .

# dacă nu mere, încearcă ”flask httpx orjson python-dotenv requests” înloc de ” -r requirements.txt”
RUN pip install --only-binary :all: --require-hashes -r requirements.txt


# dacă nu mere încearcă sa adaugi "COPY . .” sau "ADD . ."

COPY ./api ./api

#Nu cred ca este nevoie dar nici nu cred ca strica
EXPOSE 5000

# 1. Creează un utilizator și un grup fără privilegii speciale (îl numim "appuser")
RUN useradd -m appuser && chown -R appuser /app_py_ai

# 2. Schimbă proprietarul folderului de lucru către noul utilizator 
# (esențial dacă API-ul tău trebuie să scrie fișiere sau log-uri aici)


# 3. Spune-i lui Docker să ruleze comenzile următoare și containerul cu acest utilizator
USER appuser

CMD ["python", "-m", "api.api"]
