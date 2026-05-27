import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="AI Study 2026", layout="wide", page_icon="🎓")

# Relative path - rất quan trọng cho Streamlit Cloud
BASE_ROOT = os.path.dirname(os.path.abspath(__file__))
SUBJECTS_ROOT = os.path.join(BASE_ROOT, "Lession")

# ====================== DATABASE ======================
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Students
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    nickname TEXT,
                    full_name TEXT)''')
    
    # Progress
    c.execute('''CREATE TABLE IF NOT EXISTS progress (
                    student_id TEXT,
                    day_key TEXT,
                    status TEXT,
                    assigned_date TEXT,
                    completed_date TEXT,
                    submission TEXT,
                    notebooklm_link TEXT,
                    PRIMARY KEY (student_id, day_key))''')
    
    # Notes
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    note_text TEXT,
                    created_at TEXT)''')
    
    conn.commit()
    return conn

# ====================== HỖ TRỢ ======================
def get_subject_dirs():
    if not os.path.exists(SUBJECTS_ROOT):
        return []
    return sorted([d for d in os.listdir(SUBJECTS_ROOT) 
                   if os.path.isdir(os.path.join(SUBJECTS_ROOT, d))])

def format_subject_name(subject_dir):
    label = subject_dir.replace("_2026", "").replace("_", " ").strip()
    return label.title() if label else subject_dir

def get_subject_paths(subject_dir):
    base_dir = os.path.join(SUBJECTS_ROOT, subject_dir)
    data_dir = os.path.join(base_dir, "data")
    roadmap_dir = os.path.join(data_dir, "roadmap")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(roadmap_dir, exist_ok=True)
    return base_dir, data_dir, roadmap_dir

def load_lesson_content(roadmap_dir, day_key):
    lesson_file = os.path.join(roadmap_dir, f"{day_key}.md")
    if os.path.exists(lesson_file):
        with open(lesson_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def get_roadmap_days(roadmap_dir):
    if not os.path.exists(roadmap_dir):
        return []
    days = [f for f in os.listdir(roadmap_dir) if f.lower().endswith('.md')]
    days_sorted = sorted(days, key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
    return [os.path.splitext(day)[0] for day in days_sorted]

# ====================== MAIN APP ======================
subjects = get_subject_dirs()
if not subjects:
    st.error("Không tìm thấy thư mục môn học nào trong thư mục 'Lession'.")
    st.stop()

st.sidebar.title("📚 Môn học")
subject = st.sidebar.selectbox(
    "Chọn môn học",
    subjects,
    format_func=format_subject_name
)

BASE_DIR, DATA_DIR, ROADMAP_DIR = get_subject_paths(subject)
DB_PATH = os.path.join(DATA_DIR, "study.db")
conn = init_db(DB_PATH)

available_lesson_days = get_roadmap_days(ROADMAP_DIR)

st.title("🎓 AI Study 2026 - CrewAI")
st.subheader(f"Môn học: {format_subject_name(subject)}")

# ====================== PASSWORD ADMIN ======================
st.sidebar.header("🔑 Vai trò")
mode = st.sidebar.radio("", ["👨 (Admin)", "👦 (Student)"], label_visibility="collapsed")

ADMIN_PASSWORD = "123456"  # ← Bạn đổi password này thành cái mạnh hơn

if mode == "👨 (Admin)":
    password = st.sidebar.text_input("Nhập mật khẩu Admin", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("🔒 Vui lòng nhập đúng mật khẩu để vào phần Admin")
        st.stop()
    
    st.header("🔧 Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["📊 Tổng quan", "👥 Quản lý Bé", "📚 Giao Bài"])

    with tab1:
        st.subheader("Tổng quan tiến độ")
        df = pd.read_sql_query("""
            SELECT s.nickname, COUNT(CASE WHEN p.status = 'completed' THEN 1 END) as completed,
                   COUNT(p.day_key) as total_assigned
            FROM students s
            LEFT JOIN progress p ON s.id = p.student_id
            GROUP BY s.id
        """, conn)
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.subheader("Quản lý Bé")
        # Thêm bé mới
        col1, col2 = st.columns(2)
        with col1:
            new_nick = st.text_input("Nickname mới")
        with col2:
            new_full = st.text_input("Tên đầy đủ")
        if st.button("➕ Thêm bé"):
            if new_nick and new_full:
                sid = new_nick.lower().replace(" ", "_")
                conn.execute("INSERT OR IGNORE INTO students (id, nickname, full_name) VALUES (?, ?, ?)",
                           (sid, new_nick, new_full))
                conn.commit()
                st.success(f"Đã thêm {new_nick}")
            else:
                st.warning("Nhập đầy đủ thông tin")

        # Danh sách bé
        students = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(students, use_container_width=True)

    with tab3:
        st.subheader("Giao bài")
        if available_lesson_days:
            day = st.selectbox("Chọn ngày", available_lesson_days, 
                             format_func=lambda x: x.replace("day", "Ngày "))
        else:
            day = f"day{st.number_input('Ngày', min_value=1, value=1)}"

        students_list = pd.read_sql_query("SELECT id, nickname FROM students", conn)
        
        if st.button("🚀 Giao cho TẤT CẢ bé", type="primary"):
            for sid in students_list['id']:
                conn.execute("""INSERT OR REPLACE INTO progress 
                              (student_id, day_key, status, assigned_date)
                              VALUES (?, ?, 'assigned', ?)""",
                           (sid, day, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success(f"Đã giao {day} cho tất cả bé!")

# ====================== STUDENT MODE ======================
else:
    st.header("👦 Student Dashboard")
    students = pd.read_sql_query("SELECT id, nickname FROM students", conn)
    selected_sid = st.selectbox("Chọn bé", students['id'], 
                              format_func=lambda x: students[students['id']==x]['nickname'].values[0])
    
    student_name = students[students['id']==selected_sid]['nickname'].values[0]
    st.subheader(f"Xin chào {student_name} 👋")

    # Tiến độ
    progress_df = pd.read_sql_query("""
        SELECT day_key, status, assigned_date, completed_date 
        FROM progress WHERE student_id = ? 
        ORDER BY day_key
    """, conn, params=(selected_sid,))
    
    if not progress_df.empty:
        st.dataframe(progress_df, use_container_width=True)
    else:
        st.info("Chưa có bài nào được giao.")

    # Học bài
    if not progress_df.empty:
        assigned_days = progress_df['day_key'].tolist()
        selected_day = st.selectbox("📖 Chọn bài học", assigned_days, 
                                  format_func=lambda x: x.replace("day", "Ngày "))
        
        lesson_content = load_lesson_content(ROADMAP_DIR, selected_day)
        if lesson_content:
            st.markdown("---")
            st.subheader(f"Bài học {selected_day.replace('day', 'Ngày ')}")
            st.markdown(lesson_content)
        
        # Nộp bài
        st.subheader("📤 Nộp bài tập")
        submission = st.text_area("Dán code Python hoặc câu trả lời của con", height=200)
        notebook_link = st.text_input("🔗 Dán link NotebookLM (nếu có)")
        
        uploaded_file = st.file_uploader("Upload file code (.py, .ipynb, ảnh...)", type=['py', 'ipynb', 'png', 'jpg'])
        
        if st.button("✅ Hoàn thành & Nộp bài"):
            file_path = None
            if uploaded_file:
                uploads_dir = os.path.join(DATA_DIR, "uploads")
                os.makedirs(uploads_dir, exist_ok=True)
                file_path = os.path.join(uploads_dir, f"{selected_sid}_{selected_day}_{uploaded_file.name}")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            conn.execute("""INSERT OR REPLACE INTO progress 
                          (student_id, day_key, status, completed_date, submission, notebooklm_link)
                          VALUES (?, ?, 'completed', ?, ?, ?)""",
                       (selected_sid, selected_day, datetime.now().strftime("%Y-%m-%d"), 
                        submission, notebook_link))
            conn.commit()
            st.success("🎉 Con đã hoàn thành bài học!")
    
    # Ghi chú
    st.subheader("📝 Ghi chú cá nhân")
    note = st.text_area("Viết ghi chú hôm nay")
    if st.button("Lưu ghi chú"):
        if note.strip():
            conn.execute("INSERT INTO notes (student_id, note_text, created_at) VALUES (?, ?, ?)",
                        (selected_sid, note, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            st.success("Đã lưu ghi chú")

    # Hiển thị ghi chú gần đây
    notes = pd.read_sql_query("SELECT * FROM notes WHERE student_id = ? ORDER BY created_at DESC LIMIT 5",
                            conn, params=(selected_sid,))
    if not notes.empty:
        st.markdown("---")
        st.subheader("Ghi chú gần đây")
        for _, row in notes.iterrows():
            st.caption(row['created_at'])
            st.write(row['note_text'])
