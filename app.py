import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import json
import os
from PIL import Image
from io import BytesIO
import base64
import requests  # <— NOWE

# =========================
# KONFIGURACJA STRONY
# =========================
st.set_page_config(
    page_title="💪 Plan Treningowy",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# KONFIG: GitHub + lokalny plik
# =========================
# Lokalny cache (opcjonalnie — ułatwia działanie lokalne)
DATA_FILE = "gym_progress.json"

# Konfiguracja z secrets (zalecane)
GITHUB_TOKEN = st.secrets.get("github_token", None)
REPO_OWNER = st.secrets.get("repo_owner", "")
REPO_NAME = st.secrets.get("repo_name", "")
REPO_BRANCH = st.secrets.get("repo_branch", "main")
REPO_FILE_PATH = st.secrets.get("repo_file_path", "gym_progress.json")

# Pomocnicze: walidacja konfiguracji GitHub
def github_config_ok():
    return bool(GITHUB_TOKEN and REPO_OWNER and REPO_NAME and REPO_BRANCH and REPO_FILE_PATH)

def _gh_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def _gh_contents_url():
    return f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{REPO_FILE_PATH}"

# =========================
# MAPOWANIE OBRAZKÓW
# =========================
EXERCISE_IMAGES = {
    "Wyciskanie na ławeczce poziomej": "lawka.png",
    "Brzuszki na maszynie": "brzuszki.png",
    "Boczne zgięcia tułowia na ławce rzymskiej": "brzuszki-rzymska.png",
    "Skłony tułowia na ławce skośnej": "brzuszki-lawka.png",
    "Wznosy zgiętych nóg w zwisie na drążku": "brzuch-wznosy.png",
    "Wypychanie nóg (Leg Press)": "legpress.png",
    "Biceps - uginanie ramion": "biceps.png",
    "Podciąganie sztangi wzdłuż tułowia": "barki.png",
    "Odwrotne rozpiętki na maszynie": "barki-rozpietki.png",
    "Triceps - wyciskanie francuskie": "triceps.png",
    "Przenoszenie hantla za głowę w leżeniu": "wioslowanie.png",
    "Wyciskanie na suwnicy Smitha": "podciaganie.png",
    "Wyciskanie hantlii": "klata-wyciskaniehantli.png",
    "Rozpietki na maszynie": "klata-rozpietki.png",
    "Pompki na poręczach ze wspomaganiem": "klata-pompki-maszyna.png",
    # Nowe ćwiczenia
    "Przysiady na suwnicy Smitha": "brak.png",
    "Uginanie nóg leżąc": "nogi-lezac.png",
    "Uginanie nóg siedząc": "nogi-siedzac.png",
    "Odwodzenie nóg siedząc": "nogi-odwodzenie.png", 
    "Wypychanie ciężaru palcami nóg": "nogi-lydki-suwnica.png",
    "Wspięcia na palce siedząc na maszynie": "nogi-lydki.png",
    "Skręty tułowia na maszynie": "brzuch-skretytulowia.png",
    "Plank": "brak.png",
    "Wyciskanie hantli nad głowę siedząc": "barki-wyciskaniehantli.png",
    "Wyciskanie nad głowę na maszynie": "barki-wyciskaniemaszyna.png",
    "Wznosy ramion bokiem z hantlami": "barki-wznosyzhantlami.png",
    "Wznosy ramion bokiem na maszynie": "barki-wznosymaszyna.png", 
    "Podciąganie hantli wzdłuż tułowia": "barki-podciaganiehantli.png", 
    "Podciąganie nachwytem ze wspomaganiem": "plecy-podciaganie.png",
    "Wiosłowanie na wyciągu dolnym": "plecy-wioslowanie.png",
    "Unoszenie tułowia na ławce rzymskiej": "plecy-unoszenietulowia.png",
    "Ściąganie drążka wyciągu górnego": "plecy-sciaganie.png",
    "Bieżnia - 30 min": "brak.png",
    "Rower stacjonarny - 20 min": "brak.png",
    "Stepper - 15 min": "brak.png"
}

# =========================
# PLAN TYGODNIA
# =========================
WEEKLY_PLAN = {
    "Poniedziałek": {
        "title": "Poniedziałek: NOGI",
        "color": "#FFB347",
        "exercises": [
            "Wypychanie nóg (Leg Press)",
            "Uginanie nóg leżąc",
            "Uginanie nóg siedząc",
            "Odwodzenie nóg siedząc",
            "Wypychanie ciężaru palcami nóg",
            "Wspięcia na palce siedząc na maszynie"
        ]
    },
    "Wtorek": {
        "title": "Wtorek: KLATA",
        "color": "#FFB347",
        "exercises": [
            "Wyciskanie na ławeczce poziomej",
            "Wyciskanie na suwnicy Smitha",
            "Przenoszenie hantla za głowę w leżeniu",
            "Wyciskanie hantlii",
            "Rozpietki na maszynie",
            "Pompki na poręczach ze wspomaganiem"
        ]
    },
    "Środa": {
        "title": "Środa: BRZUCH",
        "color": "#FFB347",
        "exercises": [
            "Brzuszki na maszynie",
            "Skręty tułowia na maszynie",
            "Wznosy zgiętych nóg w zwisie na drążku",
            "Boczne zgięcia tułowia na ławce rzymskiej",
            "Skłony tułowia na ławce skośnej"
        ]
    },
    "Czwartek": {
        "title": "Czwartek: BARKI",
        "color": "#FFB347",
        "exercises": [
            "Podciąganie sztangi wzdłuż tułowia",
            "Wyciskanie hantli nad głowę siedząc",
            "Wznosy ramion bokiem z hantlami",
            "Wyciskanie nad głowę na maszynie",
            "Wznosy ramion bokiem na maszynie",
            "Odwrotne rozpiętki na maszynie",
            "Podciąganie hantli wzdłuż tułowia"
        ]
    },
    "Piątek": {
        "title": "Piątek: PLECY",
        "color": "#FFB347",
        "exercises": [
            "Podciąganie nachwytem ze wspomaganiem",
            "Wiosłowanie na wyciągu dolnym",
            "Ściąganie drążka wyciągu górnego",
            "Unoszenie tułowia na ławce rzymskiej"
        ]
    },
    "Sobota": {"title": "Sobota: REGENERACJA", "color": "#FFB347", "exercises": []},
    "Niedziela": {
        "title": "Niedziela: CARDIO",
        "color": "#FFB347",
        "exercises": ["Bieżnia - 30 min", "Rower stacjonarny - 20 min", "Stepper - 15 min"]
    }
}

# =========================
# OPISY ĆWICZEŃ
# =========================
EXERCISES = {
    "Wypychanie nóg (Leg Press)": {"color": "#FF6B6B", "description": "Mięsień czworogłowy uda"},
    "Uginanie nóg siedząc": {"color": "#FF6B6B", "description": "Mięśnie tylnej części uda"},
    "Uginanie nóg leżąc": {"color": "#FF6B6B", "description": "Mięśnie tylnej części uda"},
    "Odwodzenie nóg siedząc": {"color": "#FF6B6B", "description": "Mięsień pośladkowy średni i mały"},
    "Wypychanie ciężaru palcami nóg": {"color": "#FF6B6B", "description": "Mięsień brzuchaty łydki "},
    "Wspięcia na palce siedząc na maszynie": {"color": "#FF6B6B", "description": "Mięsień brzuchaty łydki "},
    "Wyciskanie na ławeczce poziomej": {"color": "#4ECDC4", "description": "Mięśnie klatki piersiowej"},
    "Wyciskanie na suwnicy Smitha": {"color": "#4ECDC4", "description": "Mięśnie klatki piersiowej"},
    "Przenoszenie hantla za głowę w leżeniu": {"color": "#4ECDC4", "description": "Mięśnie klatki piersiowej"},
    "Brzuszki na maszynie": {"color": "#45B7D1", "description": "Mięśnie brzucha"},
    "Skręty tułowia na maszynie": {"color": "#45B7D1", "description": "Mięśnie skośne brzucha"},
    "Boczne zgięcia tułowia na ławce rzymskiej": {"color": "#45B7D1", "description": "Mięśnie skośne brzucha"},
    "Skłony tułowia na ławce skośnej": {"color": "#45B7D1", "description": "Mięsień prosty brzucha"},
    "Wznosy ramion bokiem z hantlami": {"color": "#96CEB4", "description": "Boczny (środkowy) akton mięśnia naramiennego "}, 
    "Wyciskanie hantlii": {"color": "#4ECDC4", "description": "Mięśnie klatki piersiowej"},
    "Rozpietki na maszynie": {"color": "#4ECDC4", "description": "Mięśnie klatki piersiowej"},
    "Pompki na poręczach ze wspomaganiem": {"color": "#4ECDC4", "description": "Mięśnie klatki piersiowej"},
    "Wznosy zgiętych nóg w zwisie na drążku": {"color": "#45B7D1", "description": "Mięsień prosty brzucha"},
    "Podciąganie sztangi wzdłuż tułowia": {"color": "#96CEB4", "description": "Boczny i przedni akton mięśnia naramiennego"},
    "Wyciskanie hantli nad głowę siedząc": {"color": "#96CEB4", "description": "Przedni akton mięśnia naramiennego"},
    "Wyciskanie nad głowę na maszynie": {"color": "#96CEB4", "description": "Przedni akton mięśnia naramiennego"},
    "Wznosy ramion bokiem na maszynie": {"color": "#96CEB4", "description": "Boczny (środkowy) akton mięśnia naramiennego"},
    "Odwrotne rozpiętki na maszynie": {"color": "#96CEB4", "description": "Tylny akton mięśnia naramiennego"},
    "Podciąganie hantli wzdłuż tułowia": {"color": "#96CEB4", "description": "Boczny i przedni akton mięśnia naramiennego"},
    "Podciąganie nachwytem ze wspomaganiem": {"color": "#FFEAA7", "description": "Mięsień najszerszy grzbietu"},
    "Wiosłowanie na wyciągu dolnym": {"color": "#FFEAA7", "description": "Mięsień czworoboczny (szczególnie część środkowa i dolna)"},
    "Ściąganie drążka wyciągu górnego": {"color": "#FFEAA7", "description": "Mięsień najszerszy grzbietu"},
    "Unoszenie tułowia na ławce rzymskiej": {"color": "#FFEAA7", "description": "Mięśnie prostowniki grzbietu"},  
    "Bieżnia - 30 min": {"color": "#FFB347", "description": "Cardio"},
    "Rower stacjonarny - 20 min": {"color": "#FFB347", "description": "Cardio"},
    "Stepper - 15 min": {"color": "#FFB347", "description": "Cardio"}
}

# =========================
# CSS
# =========================
st.markdown("""
<style>
    .main > div { padding: 1rem; }
    .stButton > button {
        width: 100%; height: 3rem; font-size: 16px; border-radius: 10px; margin-bottom: 0.5rem;
    }
    .day-container {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px; padding: 1rem; margin-bottom: 1rem;
        border: 2px solid #dee2e6; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .day-header { font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem; text-align: center; }
    .exercise-container {
        background: white; border: 2px solid #dee2e6; border-radius: 10px;
        padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex; align-items: flex-start; gap: 1rem; min-height: 70px;
    }
    .exercise-container.completed {
        background: linear-gradient(135deg, #d4edda, #c3e6cb); border-color: #28a745;
    }
    .exercise-image-container { flex-shrink: 0; width: 160px; height: 160px; }
    .exercise-content { flex-grow: 1; display: flex; flex-direction: column; gap: 0.5rem; min-width: 0; }
    .exercise-name { font-size: 1.1rem; font-weight: 600; color: #333; line-height: 1.2; margin: 0; word-wrap: break-word; }
    .exercise-footer { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
    .exercise-description { font-size: 0.9rem; color: #666; flex-grow: 1; min-width: 0; }
    .exercise-status { font-size: 1.5rem; flex-shrink: 0; }
    .week-indicator {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white; padding: 1rem; border-radius: 15px; text-align: center;
        margin-bottom: 1rem; font-size: 1.2rem; font-weight: bold;
    }
    .metric-container { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1rem; margin: 1rem 0; }
    .metric-card {
        background: white; border-radius: 10px; padding: 1rem; text-align: center; min-width: 120px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    @media (max-width: 768px) {
        .exercise-container { padding: 0.8rem; gap: 0.8rem; }
        .exercise-image-container { width: 150px; height: 150px; }
        .exercise-name { font-size: 1rem; }
        .exercise-description { font-size: 0.85rem; }
        .exercise-status { font-size: 1.3rem; }
    }
</style>
""", unsafe_allow_html=True)

# =========================
# FUNKCJE POMOCNICZE (obrazy, daty)
# =========================
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_exercise_image_base64(exercise_name):
    image_file = EXERCISE_IMAGES.get(exercise_name, "brak.png")
    if os.path.exists(image_file):
        try:
            image = Image.open(image_file)
            image = image.resize((150, 150), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except:
            return None
    return None

def get_current_week_monday():
    today = date.today()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    return monday

def get_week_range():
    monday = get_current_week_monday()
    sunday = monday + timedelta(days=6)
    return monday, sunday

# =========================
# GITHUB: wczytywanie i zapis
# =========================
def load_from_github() -> dict:
    """Wczytaj JSON z GitHuba (gałąź/ścieżka z konfiguracji)."""
    if not github_config_ok():
        return {}
    try:
        # GET /contents/{path}?ref=branch
        url = _gh_contents_url() + f"?ref={REPO_BRANCH}"
        r = requests.get(url, headers=_gh_headers(), timeout=15)
        if r.status_code == 200:
            content_b64 = r.json().get("content", "")
            if content_b64:
                decoded = base64.b64decode(content_b64).decode("utf-8")
                return json.loads(decoded)
            return {}
        elif r.status_code == 404:
            # Plik nie istnieje — zwróć pusty słownik (utworzymy przy zapisie)
            return {}
        else:
            st.warning(f"Nie udało się wczytać danych z GitHuba: {r.status_code}")
            return {}
    except Exception as e:
        st.warning(f"Błąd połączenia z GitHub: {e}")
        return {}

def save_to_github(data_dict: dict, commit_message: str = "Update gym progress"):
    """Zapis JSON do repo GitHub: tworzy plik, jeśli nie ma; aktualizuje, jeśli jest."""
    if not github_config_ok():
        st.error("Brak konfiguracji GitHub w st.secrets — zapis tylko lokalny.")
        return False

    try:
        # Najpierw pobierz SHA (jeśli plik istnieje)
        url = _gh_contents_url()
        get_resp = requests.get(url, headers=_gh_headers(), timeout=15)
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

        json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
        encoded_content = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": commit_message,
            "content": encoded_content,
            "branch": REPO_BRANCH
        }
        if sha:
            payload["sha"] = sha  # wymagane przy aktualizacji

        put_resp = requests.put(url, headers=_gh_headers(), json=payload, timeout=15)
        if put_resp.status_code in (200, 201):
            return True
        else:
            st.error(f"❌ Błąd zapisu do GitHuba: {put_resp.status_code} - {put_resp.text}")
            return False
    except Exception as e:
        st.error(f"❌ Wyjątek przy zapisie do GitHuba: {e}")
        return False

# =========================
# DANE: warstwa pośrednia (cache + fallback)
# =========================
@st.cache_data(show_spinner=False)
def _initial_load_data():
    """Jednorazowe wczytanie danych przy starcie sesji."""
    # 1) Spróbuj z GitHuba
    gh_data = load_from_github()
    if gh_data:
        return gh_data
    # 2) Fallback: lokalny plik (np. podczas pracy lokalnej)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_data():
    # Trzymaj aktualny stan w session_state, żeby nie robić wielu requestów do GitHuba
    if "data_store" not in st.session_state:
        st.session_state.data_store = _initial_load_data()
    return st.session_state.data_store

def save_data(data, commit_message="Update gym progress"):
    """Zapis lokalny (cache + plik) + commit do GitHuba."""
    # 1) Aktualizuj cache w sesji
    st.session_state.data_store = data

    # 2) Opcjonalny zapis lokalny (przydatny lokalnie)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # Ignoruj błąd lokalny w chmurze
        pass

    # 3) Zapis do GitHuba (tworzy plik, jeśli nie istnieje)
    ok = save_to_github(data, commit_message=commit_message)
    if ok:
        st.toast("✅ Zapisano do GitHuba", icon="✅")
    return ok

# =========================
# LOGIKA ĆWICZEŃ
# =========================
def add_exercise_record(exercise_name, weight, date_str):
    data = load_data()
    if exercise_name not in data:
        data[exercise_name] = []
    record = {"date": date_str, "weight": weight}
    data[exercise_name].append(record)
    data[exercise_name] = sorted(data[exercise_name], key=lambda x: x['date'])
    # Komunikat commita z kontekstem
    commit_msg = f"Add/update record: {exercise_name} {weight} @ {date_str}"
    return save_data(data, commit_message=commit_msg)

def get_exercise_data(exercise_name):
    data = load_data()
    return data.get(exercise_name, [])

def is_exercise_completed_this_week(exercise_name):
    monday, sunday = get_week_range()
    exercise_data = get_exercise_data(exercise_name)
    for record in exercise_data:
        record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
        if monday <= record_date <= sunday:
            return True
    return False

def get_week_completion_stats():
    total_exercises = 0
    completed_exercises = 0
    for day, day_data in WEEKLY_PLAN.items():
        if day == "Sobota":
            continue
        for exercise in day_data["exercises"]:
            total_exercises += 1
            if is_exercise_completed_this_week(exercise):
                completed_exercises += 1
    completion_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
    return completed_exercises, total_exercises, completion_percentage

def create_progress_chart(exercise_name):
    data = get_exercise_data(exercise_name)
    if not data:
        st.info("🎯 Dodaj pierwsze dane, aby zobaczyć wykres postępu!")
        return

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['weight'], mode='lines+markers',
        line=dict(color=EXERCISES[exercise_name]["color"], width=4),
        marker=dict(size=10, color=EXERCISES[exercise_name]["color"], line=dict(width=2, color='white'))
    ))

    fig.update_layout(
        title=f'📈 Postęp - {exercise_name}', title_font_size=16,
        xaxis_title='Data', yaxis_title='Ciężar (kg)',
        hovermode='x unified', height=350,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False, margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    st.plotly_chart(fig, use_container_width=True)

    if len(df) > 0:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: #666;">🎯 Ostatni</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #333;">{df['weight'].iloc[-1]} kg</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: #666;">🏆 Rekord</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #333;">{df['weight'].max()} kg</div>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            progress = df['weight'].iloc[-1] - df['weight'].iloc[0] if len(df) > 1 else 0
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: #666;">📊 Postęp</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #333;">{progress:+.1f} kg</div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# STRONY
# =========================
def exercise_page(exercise_name):
    if st.button("⬅️ Powrót do planu treningowego", use_container_width=True, type="secondary"):
        st.session_state.selected_exercise = None
        st.query_params.clear()
        st.rerun()

    col1, col2 = st.columns([1, 3])
    with col1:
        image_file = EXERCISE_IMAGES.get(exercise_name, "brak.png")
        if os.path.exists(image_file):
            try:
                image = Image.open(image_file)
                image = image.resize((80, 80), Image.Resampling.LANCZOS)
                st.image(image, width=80)
            except:
                st.markdown(f"""
                <div style="width: 180px; height: 180px; border-radius: 15px; 
                           background: linear-gradient(135deg, {EXERCISES[exercise_name]['color']}30, {EXERCISES[exercise_name]['color']}160);
                           display: flex; align-items: center; justify-content: center; 
                           font-size: 2rem; color: white; margin: auto;">💪</div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="width: 180px; height: 180px; border-radius: 15px; 
                       background: linear-gradient(135deg, {EXERCISES[exercise_name]['color']}30, {EXERCISES[exercise_name]['color']}160);
                       display: flex; align-items: center; justify-content: center; 
                       font-size: 2rem; color: white; margin: auto;">💪</div>
            """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="padding-left: 1rem;">
            <h2 style="color: {EXERCISES[exercise_name]['color']}; margin-bottom: 0.5rem; font-size: 1.4rem;">{exercise_name}</h2>
            <p style="font-size: 16px; color: #666; margin-bottom: 1rem;">{EXERCISES[exercise_name]['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    with st.form(f"workout_form_{exercise_name}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            workout_date = st.date_input("📅 Data:", value=date.today())
        with col2:
            default_weight = 30.0 if "min" not in exercise_name else 0.0
            max_value = 300.0 if "min" not in exercise_name else 60.0
            step_value = 2.5 if "min" not in exercise_name else 5.0
            label = "⚖️ Ciężar (kg):" if "min" not in exercise_name else "⏱️ Czas (min):"
            weight = st.number_input(label, min_value=0.0, max_value=max_value, 
                                     value=default_weight, step=step_value, format="%.1f")
        submit_button = st.form_submit_button("💾 Zapisz trening", use_container_width=True, type="primary")

        if submit_button:
            date_str = workout_date.strftime("%Y-%m-%d")
            unit = "kg" if "min" not in exercise_name else "min"
            if add_exercise_record(exercise_name, weight, date_str):
                st.success(f"✅ Zapisano: {weight} {unit} w dniu {workout_date}")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Błąd podczas zapisywania!")

    st.markdown("---")
    create_progress_chart(exercise_name)

def main_page():
    monday, sunday = get_week_range()
    completed, total, percentage = get_week_completion_stats()
    st.markdown(f"""
    <div class="week-indicator">
        📅 Plan treningowy: {monday.strftime('%d.%m')} - {sunday.strftime('%d.%m.%Y')}<br>
        🎯 Postęp tygodnia: {completed}/{total} ćwiczeń ({percentage:.0f}%)
    </div>
    """, unsafe_allow_html=True)

    st.progress(percentage / 100)

    days_polish = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
    for day in days_polish:
        day_data = WEEKLY_PLAN[day]
        st.markdown(f"""
        <div class="day-container">
            <div class="day-header" style="color: {day_data['color']};">
                {day_data['title']}
            </div>
        """, unsafe_allow_html=True)
        
        if day == "Sobota":
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #666;">
                🛌 Dzień regeneracji<br>
                <small>Odpoczynek jest tak samo ważny jak trening!</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            for exercise in day_data["exercises"]:
                is_completed = is_exercise_completed_this_week(exercise)
                completion_icon = "✅" if is_completed else "⭕"
                completed_class = "completed" if is_completed else ""
                image_html = ""
                image_file = EXERCISE_IMAGES.get(exercise, "brak.png")
                if os.path.exists(image_file):
                    try:
                        image = Image.open(image_file); image = image.resize((160, 160), Image.Resampling.LANCZOS)
                        buffered = BytesIO(); image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        image_html = f'<img src="data:image/png;base64,{img_str}" style="width: 160px; height: 160px; border-radius: 8px; object-fit: cover; border: 2px solid #f8f9fa;">'
                    except:
                        image_html = f"""
                        <div style="width: 160px; height: 160px; border-radius: 8px; 
                                   background: linear-gradient(135deg, {day_data['color']}30, {day_data['color']}160);
                                   display: flex; align-items: center; justify-content: center; 
                                   font-size: 1.8rem; color: white; flex-shrink: 0;">💪</div>
                        """
                else:
                    image_html = f"""
                    <div style="width: 160px; height: 160px; border-radius: 8px; 
                               background: linear-gradient(135deg, {day_data['color']}30, {day_data['color']}160);
                               display: flex; align-items: center; justify-content: center; 
                               font-size: 1.8rem; color: white; flex-shrink: 0;">💪</div>
                    """
                st.markdown(f"""
                <div class="exercise-container {completed_class}">
                    <div class="exercise-image-container">{image_html}</div>
                    <div class="exercise-content">
                        <div class="exercise-name">{exercise}</div>
                        <div class="exercise-footer">
                            <div class="exercise-description">{EXERCISES[exercise]['description']}</div>
                            <div class="exercise-status">{completion_icon}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                exercise_short = exercise.split(' - ')[0][:30] + "..." if len(exercise) > 30 else exercise
                if st.button(f"➤ {exercise_short}", key=f"{day}_{exercise}", use_container_width=True):
                    st.session_state.selected_exercise = exercise
                    st.query_params["exercise"] = exercise
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# INICJALIZACJA
# =========================
if 'selected_exercise' not in st.session_state:
    st.session_state.selected_exercise = None

# Jednorazowy „start” — wczytaj dane do cache
_ = load_data()

# Parametry URL
params = st.query_params
if "exercise" in params:
    exercise_name = params["exercise"]
    if exercise_name in EXERCISES:
        st.session_state.selected_exercise = exercise_name

# =========================
# GŁÓWNA LOGIKA
# =========================
if st.session_state.selected_exercise is not None:
    exercise_page(st.session_state.selected_exercise)
else:
    main_page()
