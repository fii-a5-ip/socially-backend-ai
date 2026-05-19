# 🧠 Documentație Tehnică: Modul Onboarding AI & Profilare Lifestyle

## 📌 1. Descrierea Modulului
Sistemul de Onboarding este o mașină de stări (State Machine) alimentată de AI, concepută pentru a extrage preferințele de lifestyle, buget și logistică ale unui utilizator prin intermediul unei conversații naturale în 3 pași. 

Sistemul evită efectul de "Tunnel Vision" prin utilizarea unor **întrebări multi-dimensionale** și a unei reguli de **Cross-Profiling** (schimbarea obligatorie a subiectului la fiecare pas), obținând un profil 360° (vibe, transport, dietă, activități) din doar 3 interacțiuni.

---

## ⚙️ 2. Specificații API și Mod de Utilizare

* **Endpoint:** `/api/onboardingProcess`
* **Metodă:** `POST`
* **Content-Type:** `application/json`

*(Notă pentru Backend-Core: Acest endpoint este "stateless". Asta înseamnă că Backend-AI-ul nu ține minte conversația între request-uri. Este responsabilitatea Backend-Core-ului să stocheze și să trimită istoricul complet la fiecare apel).*

### Faza 1: Inițializarea (Pasul 0 - Formularul de start)
Se execută o singură dată, imediat după ce utilizatorul completează formularul inițial (nume, vârstă, ocupație). 
**Atenție:** La acest pas NU se apelează AI-ul. Backend-AI-ul folosește un algoritm intern de parsare pentru a calcula automat un profil de bază și a returna prima întrebare hiper-personalizată.

**📥 Input trimis de Backend-Core:**
```json
{
    "step": 0,
    "user_info": {
        "nume": "Alex",
        "varsta": 21,
        "ocupatie": "student",
        "oras": "Iași",
        "is_remote": false
    }
}
```

**📤 Output returnat de Backend-AI:**
Backend-Core-ul trebuie doar să ia valoarea din `question_text` și să o afișeze ca prim mesaj al AI-ului în interfața de chat.
```json
{
    "status": "start",
    "next_step": 1,
    "current_question_id": "L1-AA",
    "question_text": "Salut! Ca student în Iași, ai o groază de opțiuni. Cum îți definești stilul general de viață în afara facultății? Ești genul care este mereu în centrul acțiunii la petreceri, sau te consideri o fire mai degrabă 'chill'?"
}
```

---

### Faza 2: Conversația AI (Pașii 1, 2 și 3)
Aici începe interacțiunea reală cu motorul AI (LLM). Utilizatorul răspunde la întrebarea de pe ecran, iar Backend-Core-ul trebuie să împacheteze Perechea (Întrebare + Răspuns) și să o trimită la Backend-AI.

**REGULA DE AUR PENTRU Backend-Core:** Array-ul `conversation_history` trebuie să se acumuleze cu fiecare pas!
* La `step: 1` trimiți **1 pereche** {q, a}.
* La `step: 2` trimiți **2 perechi** {q, a}.
* La `step: 3` trimiți **3 perechi** {q, a}.

**📥 Exemplu Input la Pasul 1:**
```json
{
    "step": 1, 
    "conversation_history": [
        {
            "q": "Salut! Ca student în Iași... [textul complet al primei întrebări]",
            "a": "Îmi place să ies cu colegii la o bere rece pe o terasă în Copou..."
        }
    ]
}
```

**📤 Output Intermediar (Primit la Pașii 1 și 2):**
Backend-AI-ul returnează statusul `continue` și următoarea întrebare pe care Backend-Core-ul o va afișa pe ecran.
```json
{
    "status": "continue",
    "next_step": 2,
    "next_question_id": "L2-C",
    "next_question_text": "Pentru o cină ideală, preferi să conduci spre un fine dining sau...",
    "current_filters": ["cafe", "free_wifi", "terrace"]
}
```

**📥 Exemplu Input la Pasul 2 (Istoricul a crescut!):**
```json
{
    "step": 2, 
    "conversation_history": [
        {
            "q": "Salut! Ca student în Iași...",
            "a": "Îmi place să ies cu colegii la o bere..."
        },
        {
            "q": "Pentru o cină ideală, preferi să conduci spre un fine dining sau...",
            "a": "Aș alege mereu fine dining, dar nu am mașină deci merg pe jos."
        }
    ]
}
```

**📤 Output Final (Primit la Pasul 3):**
Când conversația se termină (după ce user-ul a trimis și al 3-lea răspuns), Backend-AI-ul schimbă statusul în `complete`. În acest moment, Backend-Core-ul poate închide modulul de chat și poate salva profilul.
```json
{
    "status": "complete",
    "final_filters": ["cafe", "free_wifi", "terrace", "fine_dining"]
}
```

---

## 🧠 3. Cum „Gândește” Motorul AI (Arhitectura Promptului)

Motorul AI este configurat pe modelul `llama3-70b-8192` cu **`temperature=0.0`**. Aceasta îl transformă dintr-un generator creativ de text într-un **extractor de date rece și analitic**, eliminând halucinațiile.

Comportamentul său este dictat de următoarele principii inginerești inserate în Prompt:

### A. Tehnica „Chain of Thought” (Analiza Logică)
Modelul este obligat să returneze un obiect JSON care începe cu cheia `"analiza_logica"`. Forțând AI-ul să scrie un plan de acțiune *înainte* de a lista filtrele, prevenim erorile. El trebuie să justifice de ce a extras un filtru și de ce a ignorat altul.

### B. Memoria Completă (Cumularea Filtrelor)
Deoarece LLM-urile suferă de *Recency Bias* (uită începutul conversației și se focusează doar pe ultimul mesaj), AI-ul a fost instruit să analizeze de fiecare dată **tot istoricul** primit și să facă un „merge” (o îmbinare) al tuturor preferințelor validate până la pasul curent. Acesta este motivul pentru care Backend-Core-ul trebuie să trimită mereu array-ul complet.

### C. Prioritatea Temporală (Răzgândirea)
Dacă utilizatorul se contrazice (ex. la Pasul 1 cere carne, la Pasul 3 zice că e vegetarian), AI-ul acordă prioritate absolută ultimului răspuns și **elimină** din array filtrele anterioare care intră în conflict direct.

### D. Intenție vs. Mențiune Pasivă
AI-ul este antrenat să ignore „zgomotul de fond”. Dacă utilizatorul spune: *"Urăsc cluburile, vreau în parc"*, modelul nu va extrage filtrul `nightclub`, deoarece identifică subiectul propoziției ca fiind o excludere/plângere, nu o intenție de consum.

### E. Răspunsuri de tip Troll / Skip
Dacă utilizatorul depășește limita de 30 de caractere dar scrie un text evaziv (ex: *"Sincer nu știu ce vreau, dați-mi următoarea întrebare"*), AI-ul are instrucțiuni stricte să returneze un array gol `[]` și să nu inventeze filtre de umplutură.

---

## 📐 4. Ghid de mentenanță (Pentru viitorii Developeri)

Dacă dorești să modifici sau să adaugi elemente în sistem, respectă aceste reguli:

1. **Adăugarea de Filtre Noi (`filters2.txt`):**
   * Păstrează mereu un format curat. Dacă AI-ul confundă termeni românești, folosește formatul dicționar: `id_filtru (sinonim1, sinonim2)`. Ex: `step-free access (fără trepte, rampă)`.
   * Adaugă filtre negative pentru excluderi clare (`no pets allowed`, `alcohol free`).

2. **Modificarea Întrebărilor (`onboarding_questions.json`):**
   * **Nu scrie întrebări Uni-dimensionale** (ex: *„Îți place cafeaua?”*). Asta duce la „Tunnel Vision”.
   * **Scrie întrebări Multi-dimensionale** (ex: *„Vrei să conduci până la o cafenea scumpă în natură, sau să mergi pe jos la magazinul de la colț?”*). Asta extrage 4 concepte simultan: Transport, Buget, Locație, Produs.

3. **Manevrarea Erorilor (Rate Limits):**
   * Dacă platforma Groq atinge limita de tokeni, va returna un cod HTTP `429 Too Many Requests`. În producție, asigurați-vă că pe funcția de call către AI există o logică de `Exponential Backoff` (reîncercare automată după 2, 4, 8 secunde).