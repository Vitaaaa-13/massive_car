import streamlit as st
import sqlite3
import os
import fitz
from docx import Document
from io import BytesIO

st.set_page_config(page_title="DocAssist AI", layout="wide")
st.title("DocAssist AI — помощник по работе с документами")

# --- БАЗА ДАННЫХ ---
def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/docassist.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, doc_name TEXT, loc TEXT, text TEXT)''')
    conn.commit()
    conn.close()

def parse_docs():
    conn = sqlite3.connect('data/docassist.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM chunks')
    if c.fetchone()[0] > 0:
        conn.close()
        return
    seed_dir = 'data/seed'
    if not os.path.exists(seed_dir): return
    for filename in os.listdir(seed_dir):
        filepath = os.path.join(seed_dir, filename)
        if filename.lower().endswith('.pdf'):
            doc = fitz.open(filepath)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    c.execute("INSERT INTO chunks (doc_name, loc, text) VALUES (?, ?, ?)", (filename, f"стр. {page_num+1}", text))
        elif filename.lower().endswith('.docx'):
            try:
                doc = Document(filepath)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                for table in doc.tables:
                    for row in table.rows:
                        text += "\n" + " | ".join([cell.text for cell in row.cells])
                if text.strip():
                    c.execute("INSERT INTO chunks (doc_name, loc, text) VALUES (?, ?, ?)", (filename, "текст", text))
            except Exception: pass
    conn.commit()
    conn.close()

init_db()
parse_docs()

# --- ЛОГИКА ЧАТА ---
def generate_response(prompt, history):
    p = prompt.lower().strip()
    last_bot_msg = history[-2]["content"].lower() if len(history) >= 2 else ""
    
    if "рабоч" in p and "групп" in p:
        return "Для правильного маршрута необходимо уточнить: эта рабочая группа создается для ИТ-проекта или для решения вопросов, связанных с информационными системами? (Ответьте «Да» или «Нет»)"
    
    if ("да" in p or "нет" in p) and "эта рабочая группа создается для ит-проекта" in last_bot_msg:
        if "да" in p:
            return "Вы указали, что рабочая группа создается для ИТ-проекта. Согласно Матрице обязательного визирования (строка 6):\n\n*   **Юридическое подразделение:** Нет\n*   **Департамент ДОУ:** Да\n*   **Кадровое подразделение:** Да\n*   **Департамент ИТ:** Да\n\n*Применяется общий порядок Инструкции.*"
        else:
            return "Вы указали, что рабочая группа НЕ для ИТ. Согласно Матрице:\n\n*   **Юридическое подразделение:** Нет\n*   **Департамент ДОУ:** Да\n*   **Кадровое подразделение:** Да\n*   **Департамент ИТ:** Нет\n\n*Применяется общий порядок Инструкции.*"

    results = search_db(prompt)
    if not results:
        return "В базе знаний не найдено информации. Попробуйте переформулировать."
    
    answer = "На основе документов я нашел следующую информацию:\n\n"
    for doc, loc, text in results:
        answer += f"> {text[:300]}...\n\n*Источник: {doc}, {loc}*\n\n"
    return answer

def search_db(query):
    conn = sqlite3.connect('data/docassist.db')
    c = conn.cursor()
    words = query.lower().split()
    if not words: return []
    conditions = " OR ".join(["LOWER(text) LIKE ?" for _ in words])
    params = [f"%{w}%" for w in words]
    c.execute(f"SELECT doc_name, loc, text FROM chunks WHERE {conditions} LIMIT 2", params)
    results = c.fetchall()
    conn.close()
    return results

# --- ГЕНЕРАЦИЯ DOCX ---
def create_docx(goal, subject, leader, secretary, deadline):
    seed_dir = "data/seed"
    template_path = None
    available_files = []
    
    if os.path.exists(seed_dir):
        available_files = os.listdir(seed_dir)
        for f in available_files:
            if f.lower().endswith(".docx") and ("групп" in f.lower() or "рабоч" in f.lower()):
                template_path = os.path.join(seed_dir, f)
                break
                
    if not template_path:
        return None, available_files
        
    doc = Document(template_path)
    
    for p in doc.paragraphs:
        if "О создании рабочей группы по" in p.text:
            p.text = f"О создании рабочей группы по {subject}"
        if "В целях" in p.text:
            p.text = f"В целях {goal}"
        if "1. Создать рабочую группу по" in p.text:
            p.text = f"1. Создать рабочую группу по {subject}"
        if "2. Рабочей группе до" in p.text:
            p.text = f"2. Рабочей группе до {deadline} подготовить результаты и представить их руководству."
    
    for table in doc.tables:
        for row in table.rows:
            if "Руководитель" in row.cells[0].text:
                row.cells[1].text = leader
            if "Секретарь" in row.cells[0].text:
                row.cells[1].text = secretary

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio, []

# --- ИНТЕРФЕЙС ---
if "my_docx" not in st.session_state:
    st.session_state.my_docx = None
    st.session_state.my_files = []

with st.sidebar:
    st.header("📄 Генератор DOCX")
    st.write("Заполните поля для создания черновика Распоряжения о рабочей группе.")
    
    with st.form("docx_form"):
        goal = st.text_input("Цель (В целях...)", "подготовки плана внедрения")
        subject = st.text_input("Предмет (Наименование группы)", "внедрению новой CRM")
        leader = st.text_input("Руководитель (Должность, ФИО)", "Директор департамента, И.И. Иванов")
        secretary = st.text_input("Секретарь (Должность, ФИО)", "Главный специалист, А.А. Петрова")
        deadline = st.text_input("Срок", "01.12.2026")
        
        submitted = st.form_submit_button("Сформировать DOCX")
        
        if submitted:
            docx_file, files = create_docx(goal, subject, leader, secretary, deadline)
            if docx_file:
                st.session_state.my_docx = docx_file
                st.session_state.my_files = []
            else:
                st.session_state.my_docx = None
                st.session_state.my_files = files

    # Вывод результата ВНЕ формы
    if st.session_state.my_docx:
        st.success("Документ готов!")
        st.download_button(
            label="⬇️ Скачать DOCX",
            data=st.session_state.my_docx,
            file_name="Распоряжение_Рабочая_группа.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        st.caption("⚠️ Черновик. Не является подписанным документом.")
    elif st.session_state.my_files:
        st.error("Шаблон не найден. Программа видит эти файлы:")
        st.write(st.session_state.my_files)

# Чат
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Задайте вопрос по документам..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = generate_response(prompt, st.session_state.messages)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})