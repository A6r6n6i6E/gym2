import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import json
import os
from PIL import Image
from io import BytesIO
import base64

# Konfiguracja strony
st.set_page_config(
    page_title="💪 Plan Treningowy",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ścieżka do pliku z danymi
DATA_FILE = "gym_progress.json"

# Mapowanie nazw ćwiczeń do plików PNG
EXERCISE_IMAGES = {
    "Wyciskanie na ławeczce poziomej": "lawka.png",
    "Brzuszki na maszynie": "brzuszki.png",
    "Wypychanie nóg (Leg Press)": "legpress.png",
    "Biceps - uginanie ramion": "biceps.png",
    "Barki - podciąganie sztangi": "barki.png",
    "Triceps - wyciskanie francuskie": "triceps.png",
    "Przenoszenie hantla za głowę w leżeniu": "wioslowanie.png",
    "Wyciskanie na suwnicy Smitha": "podciaganie.png",
    # Nowe ćwiczenia
    "Przysiady na suwnicy Smitha": "brak.png",
    "Uginanie nóg leżąc": "brak.png",
    "Unoszenie nóg w zwisie": "brak.png",
    "Plank": "brak.png",
    "Wyciskanie sztangi nad głowę": "brak.png",
    "Wznosy bokiem": "brak.png",
    "Podciąganie na drążku": "brak.png",
    "Wiosłowanie sztangą": "brak.png",
    "Ściąganie wyciągu górnego": "brak.png",
    "Bieżnia - 30 min": "brak.png",
    "Rower stacjonarny - 20 min": "brak.png",
    "Stepper - 15 min": "brak.png"
}

# Plan treningowy na tydzień
WEEKLY_PLAN = {
    "Poniedziałek": {
        "title": "🦵 NOGI",
        "color": "#FF6B6B",
        "exercises": [
            "Wypychanie nóg (Leg Press)",
            "Przysiady na suwnicy Smitha",
            "Uginanie nóg leżąc"
        ]
    },
    "Wtorek": {
        "title": "💪 KLATKA PIERSIOWA",
        "color": "#4ECDC4",
        "exercises": [
            "Wyciskanie na ławeczce poziomej",
            "Wyciskanie na suwnicy Smitha",
            "Przenoszenie hantla za głowę w leżeniu"
        ]
    },
    "Środa": {
        "title": "🎯 BRZUCH",
        "color": "#45B7D1",
        "exercises": [
            "Brzuszki na maszynie",
            "Unoszenie nóg w zwisie",
            "Plank"
        ]
    },
    "Czwartek": {
        "title": "🏋️ BARKI",
        "color": "#96CEB4",
        "exercises": [
            "Barki - podciąganie sztangi",
            "Wyciskanie sztangi nad głowę",
            "Wznosy bokiem"
        ]
    },
    "Piątek": {
        "title": "🔙 PLECY",
        "color": "#FFEAA7",
        "exercises": [
            "Podciąganie na drążku",
            "Wiosłowanie sztangą",
            "Ściąganie wyciągu górnego"
        ]
    },
    "Sobota": {
        "title": "😴 REGENERACJA",
        "color": "#DDA0DD",
        "exercises": []
    },
    "Niedziela": {
        "title": "🏃 CARDIO",
        "color": "#FFB347",
        "exercises": [
            "Bieżnia - 30 min",
            "Rower stacjonarny - 20 min",
            "Stepper - 15 min"
        ]
    }
}

# Rozszerzone ćwiczenia z opisami
EXERCISES = {
    "Wypychanie nóg (Leg Press)": {"color": "#FF6B6B", "description": "Czworogłowy uda"},
    "Przysiady na suwnicy Smitha": {"color": "#FF6B6B", "description": "Nogi, pośladki"},
    "Uginanie nóg leżąc": {"color": "#FF6B6B", "description": "Dwugłowy uda"},
    "Wyciskanie na ławeczce poziomej": {"color": "#4ECDC4", "description": "Klatka piersiowa"},
    "Wyciskanie na suwnicy Smitha": {"color": "#4ECDC4", "description": "Klatka piersiowa"},
    "Przenoszenie hantla za głowę w leżeniu": {"color": "#4ECDC4", "description": "Klatka piersiowa"},
    "Brzuszki na maszynie": {"color": "#45B7D1", "description": "Mięśnie brzucha"},
    "Unoszenie nóg w zwisie": {"color": "#45B7D1", "description": "Dolne brzuszki"},
    "Plank": {"color": "#45B7D1", "description": "Core stability"},
    "Barki - podciąganie sztangi": {"color": "#96CEB4", "description": "Barki"},
    "Wyciskanie sztangi nad głowę": {"color": "#96CEB4", "description": "Barki"},
    "Wznosy bokiem": {"color": "#96CEB4", "description": "Środkowe barki"},
    "Podciąganie na drążku": {"color": "#FFEAA7", "description": "Plecy, biceps"},
    "Wiosłowanie sztangą": {"color": "#FFEAA7", "description": "Plecy"},
    "Ściąganie wyciągu górnego": {"color": "#FFEAA7", "description": "Najszersze grzbietu"},
    "Bieżnia - 30 min": {"color": "#FFB347", "description": "Cardio"},
    "Rower stacjonarny - 20 min": {"color": "#FFB347", "description": "Cardio"},
    "Stepper - 15 min": {"color": "#FFB347", "description": "Cardio"}
}

# Custom CSS dla mobile-first design
st.markdown("""
<style>
    .main > div {
        padding: 1rem;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 16px;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    .day-container {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 2px solid #dee2e6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .day-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .exercise-container {
        background: white;
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        min-height: 70px;
    }
    .exercise-container.completed {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border-color: #28a745;
    }
    .exercise-image-container {
        flex-shrink: 0;
        width: 160px;
        height: 160px;
    }
    .exercise-content {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        min-width: 0;
    }
    .exercise-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #333;
        line-height: 1.2;
        margin: 0;
        word-wrap: break-word;
    }
    .exercise-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
    }
    .exercise-description {
        font-size: 0.9rem;
        color: #666;
        flex-grow: 1;
        min-width: 0;
    }
    .exercise-status {
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    .week-indicator {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        min-width: 120px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Media queries for better responsive design */
    @media (max-width: 768px) {
        .exercise-container {
            padding: 0.8rem;
            gap: 0.8rem;
        }
        .exercise-image-container {
            width: 150px;
            height: 150px;
        }
        .exercise-name {
            font-size: 1rem;
        }
        .exercise-description {
            font-size: 0.85rem;
        }
        .exercise-status {
            font-size: 1.3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Funkcje pomocnicze
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_exercise_image_base64(exercise_name):
    """Zwraca obraz ćwiczenia w formacie base64 lub None"""
    image_file = EXERCISE_IMAGES.get(exercise_name, "brak.png")
    if os.path.exists(image_file):
        try:
            image = Image.open(image_file)
            # Resize obrazka do jednolitego rozmiaru
            image = image.resize((150, 150), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except:
            return None
    return None

def get_current_week_monday():
    """Zwraca poniedziałek obecnego tygodnia"""
    today = date.today()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    return monday

def get_week_range():
    """Zwraca zakres dat obecnego tygodnia"""
    monday = get_current_week_monday()
    sunday = monday + timedelta(days=6)
    return monday, sunday

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def add_exercise_record(exercise_name, weight, date_str):
    data = load_data()
    if exercise_name not in data:
        data[exercise_name] = []
    record = {"date": date_str, "weight": weight}
    data[exercise_name].append(record)
    data[exercise_name] = sorted(data[exercise_name], key=lambda x: x['date'])
    return save_data(data)

def get_exercise_data(exercise_name):
    data = load_data()
    return data.get(exercise_name, [])

def is_exercise_completed_this_week(exercise_name):
    """Sprawdza czy ćwiczenie zostało wykonane w obecnym tygodniu"""
    monday, sunday = get_week_range()
    exercise_data = get_exercise_data(exercise_name)
    
    for record in exercise_data:
        record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
        if monday <= record_date <= sunday:
            return True
    return False

def get_week_completion_stats():
    """Zwraca statystyki ukończenia tygodnia"""
    total_exercises = 0
    completed_exercises = 0
    
    for day, day_data in WEEKLY_PLAN.items():
        if day == "Sobota":  # Sobota to regeneracja
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
        x=df['date'],
        y=df['weight'],
        mode='lines+markers',
        line=dict(color=EXERCISES[exercise_name]["color"], width=4),
        marker=dict(size=10, color=EXERCISES[exercise_name]["color"], line=dict(width=2, color='white'))
    ))

    fig.update_layout(
        title=f'📈 Postęp - {exercise_name}',
        title_font_size=16,
        xaxis_title='Data',
        yaxis_title='Ciężar (kg)',
        hovermode='x unified',
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    st.plotly_chart(fig, use_container_width=True)

    # Metryki w responsywnych kartach
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

def exercise_page(exercise_name):
    # Przycisk powrotu na górze
    if st.button("⬅️ Powrót do planu treningowego", use_container_width=True, type="secondary"):
        st.session_state.selected_exercise = None
        st.query_params.clear()
        st.rerun()

    # Nagłówek z obrazkiem
    col1, col2 = st.columns([1, 3])
    with col1:
        # Próba załadowania obrazka
        image_file = EXERCISE_IMAGES.get(exercise_name, "brak.png")
        if os.path.exists(image_file):
            try:
                image = Image.open(image_file)
                image = image.resize((80, 80), Image.Resampling.LANCZOS)
                st.image(image, width=80)
            except:
                # Fallback emoji
                st.markdown(f"""
                <div style="width: 180px; height: 180px; border-radius: 15px; 
                           background: linear-gradient(135deg, {EXERCISES[exercise_name]['color']}30, {EXERCISES[exercise_name]['color']}160);
                           display: flex; align-items: center; justify-content: center; 
                           font-size: 2rem; color: white; margin: auto;">💪</div>
                """, unsafe_allow_html=True)
        else:
            # Fallback emoji jeśli nie ma pliku
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

    # Formularz dodawania rekordu
    with st.form(f"workout_form_{exercise_name}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            workout_date = st.date_input("📅 Data:", value=date.today())
        with col2:
            # Różne wartości domyślne dla cardio vs siłowe
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
    # Nagłówek z informacją o tygodniu
    monday, sunday = get_week_range()
    completed, total, percentage = get_week_completion_stats()
    
    st.markdown(f"""
    <div class="week-indicator">
        📅 Plan treningowy: {monday.strftime('%d.%m')} - {sunday.strftime('%d.%m.%Y')}<br>
        🎯 Postęp tygodnia: {completed}/{total} ćwiczeń ({percentage:.0f}%)
    </div>
    """, unsafe_allow_html=True)

    # Pasek postępu tygodnia
    progress_bar = st.progress(percentage / 100)
    
    # Plan treningowy na każdy dzień
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
            # Ćwiczenia dla danego dnia
            for exercise in day_data["exercises"]:
                is_completed = is_exercise_completed_this_week(exercise)
                completion_icon = "✅" if is_completed else "⭕"
                completed_class = "completed" if is_completed else ""
                
                # Przygotowanie obrazka
                image_html = ""
                image_file = EXERCISE_IMAGES.get(exercise, "brak.png")
                if os.path.exists(image_file):
                    try:
                        image = Image.open(image_file)
                        image = image.resize((160, 160), Image.Resampling.LANCZOS)
                        buffered = BytesIO()
                        image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        image_html = f'<img src="data:image/png;base64,{img_str}" style="width: 160px; height: 160px; border-radius: 8px; object-fit: cover; border: 2px solid #f8f9fa;">'
                    except:
                        # Fallback emoji
                        image_html = f"""
                        <div style="width: 160px; height: 160px; border-radius: 8px; 
                                   background: linear-gradient(135deg, {day_data['color']}30, {day_data['color']}160);
                                   display: flex; align-items: center; justify-content: center; 
                                   font-size: 1.8rem; color: white; flex-shrink: 0;">💪</div>
                        """
                else:
                    # Fallback emoji jeśli nie ma pliku
                    image_html = f"""
                    <div style="width: 160px; height: 160px; border-radius: 8px; 
                               background: linear-gradient(135deg, {day_data['color']}30, {day_data['color']}160);
                               display: flex; align-items: center; justify-content: center; 
                               font-size: 1.8rem; color: white; flex-shrink: 0;">💪</div>
                    """
                
                # Kompletny HTML dla ćwiczenia
                st.markdown(f"""
                <div class="exercise-container {completed_class}">
                    <div class="exercise-image-container">
                        {image_html}
                    </div>
                    <div class="exercise-content">
                        <div class="exercise-name">{exercise}</div>
                        <div class="exercise-footer">
                            <div class="exercise-description">{EXERCISES[exercise]['description']}</div>
                            <div class="exercise-status">{completion_icon}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Przycisk dla funkcjonalności
                exercise_short = exercise.split(' - ')[0][:30] + "..." if len(exercise) > 30 else exercise
                if st.button(f"➤ {exercise_short}", key=f"{day}_{exercise}", use_container_width=True):
                    st.session_state.selected_exercise = exercise
                    st.query_params["exercise"] = exercise
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# Inicjalizacja session state
if 'selected_exercise' not in st.session_state:
    st.session_state.selected_exercise = None

# Obsługa parametrów URL
params = st.query_params
if "exercise" in params:
    exercise_name = params["exercise"]
    if exercise_name in EXERCISES:
        st.session_state.selected_exercise = exercise_name

# Główna logika
if st.session_state.selected_exercise is not None:
    exercise_page(st.session_state.selected_exercise)
else:
    main_page()
