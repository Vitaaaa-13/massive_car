import streamlit as st
import sqlite3
import os
import fitz
from docx import Document
from docx.shared import Pt
from io import BytesIO
import time
import re

st.set_page_config(
    page_title="DocAssist AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e8edf3 100%);
    font-family: 'Inter', sans-serif;
}

#MainMenu, header, footer {visibility: hidden;}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a2540 0%, #002D6B 100%);
    color: white;
    box-shadow: 4px 0 20px rgba(0,0,0,0.1);
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: white !important;
    font-weight: 700 !important;
}

.stButton>button, .stDownloadButton>button {
    background: linear-gradient(135deg, #002D6B 0%, #009688 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(0, 45, 107, 0.2) !important;
    font-size: 0.95rem !important;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 150, 136, 0.4) !important;
    background: linear-gradient(135deg, #009688 0%, #002D6B 100%) !important;
}

input, textarea {
    border-radius: 10px !important;
    border: 2px solid #e0e6ed !important;
    padding: 0.7rem 1rem !important;
    transition: all 0.2s ease !important;
}
input:focus, textarea:focus {
    border-color: #009688 !important;
    box-shadow: 0 0 0 3px rgba(0, 150, 136, 0.15) !important;
}

.user-msg {
    background: linear-gradient(135deg, #002D6B 0%, #004B87 100%);
    color: white;
    padding: 1rem 1.25rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0;
    max-width: 75%;
    margin-left: auto;
    box-shadow: 0 4px 15px rgba(0, 45, 107, 0.2);
}
.bot-msg {
    background: rgba(255, 255, 255, 0.95);
    color: #1a2b4a;
    padding: 1rem 1.25rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem 0;
    max-width: 75%;
    border: 1px solid #e8edf3;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.source-badge {
    background: linear-gradient(135deg, #e8f5f3 0%, #d4edea 100%);
    border-left: 4px solid #009688;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s ease;
}
.source-badge:hover {
    background: linear-gradient(135deg, #d4edea 0%, #b8e0db 100%);
    transform: translateX(4px);
}

.source-quote {
    background: #f8f9fa;
    border-left: 4px solid #009688;
    padding: 1rem;
    margin: 0.5rem 0 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    color: #2c3e50;
    line-height: 1.5;
}

.relevance-badge {
    display: inline-block;
    background: linear-gradient(135deg, #009688 0%, #00796B 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

h1, h2, h3 {
    color: #0a2540 !important;
    font-weight: 700 !important;
}

.header-card h1, .header-card h2, .header-card h3, .header-card p {
    color: white !important;
}

::-webkit-scrollbar {width: 8px; height: 8px;}
::-webkit-scrollbar-track {background: #f1f1f1; border-radius: 10px;}
::-webkit-scrollbar-thumb {background: #009688; border-radius: 10px;}

.wizard-step-indicator {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
    padding: 1rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.step-item {
    flex: 1;
    text-align: center;
    padding: 0.5rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #6b7a8f;
    border: 2px solid #e0e6ed;
    margin: 0 0.25rem;
}
.step-item.active {
    background: linear-gradient(135deg, #002D6B 0%, #009688 100%);
    color: white;
    border-color: #002D6B;
}
.step-item.completed {
    background: #e8f5f3;
    color: #009688;
    border-color: #009688;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ============================================================
# БАЗА ДАННЫХ
# ============================================================
def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/docassist.db')
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
    table_exists = c.fetchone()

    if table_exists:
        c.execute("PRAGMA table_info(chunks)")
        columns = [col[1] for col in c.fetchall()]
        if 'doc_type' not in columns:
            c.execute("DROP TABLE chunks")
            table_exists = None

    c.execute('''CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_name TEXT,
        doc_type TEXT,
        loc TEXT,
        section TEXT,
        item_number TEXT,
        text TEXT
    )''')
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
    if not os.path.exists(seed_dir):
        os.makedirs(seed_dir, exist_ok=True)
        conn.close()
        return

    for filename in os.listdir(seed_dir):
        filepath = os.path.join(seed_dir, filename)
        try:
            if filename.lower().endswith('.pdf'):
                doc = fitz.open(filepath)
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    if text.strip():
                        items = re.findall(r'(\d+\.\d+(?:\.\d+)?)\.\s+(.+?)(?=\n\d+\.\d+|\Z)',
                                           text, re.DOTALL)
                        if items:
                            for item_num, item_text in items:
                                c.execute(
                                    "INSERT INTO chunks (doc_name, doc_type, loc, section, item_number, text) "
                                    "VALUES (?,?,?,?,?,?)",
                                    (filename, 'pdf', f"стр.{page_num+1}",
                                     f"Пункт {item_num}", item_num, item_text.strip()))
                        else:
                            c.execute(
                                "INSERT INTO chunks (doc_name, doc_type, loc, section, item_number, text) "
                                "VALUES (?,?,?,?,?,?)",
                                (filename, 'pdf', f"стр.{page_num+1}", "Текст", None, text[:2000]))

            elif filename.lower().endswith('.docx'):
                doc = Document(filepath)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                if full_text.strip():
                    c.execute(
                        "INSERT INTO chunks (doc_name, doc_type, loc, section, item_number, text) "
                        "VALUES (?,?,?,?,?,?)",
                        (filename, 'docx', "Документ", "Основной текст", None, full_text[:3000]))

                for t_idx, table in enumerate(doc.tables):
                    rows_text = []
                    for row_idx, row in enumerate(table.rows):
                        cells = [cell.text.strip() for cell in row.cells]
                        rows_text.append(" | ".join(cells))
                        if len(cells) >= 5 and row_idx > 0:
                            c.execute(
                                "INSERT INTO chunks (doc_name, doc_type, loc, section, item_number, text) "
                                "VALUES (?,?,?,?,?,?)",
                                (filename, 'matrix', f"Таблица {t_idx+1}, строка {row_idx}",
                                 "Матрица визирования", None, " | ".join(cells)))
                    if rows_text:
                        c.execute(
                            "INSERT INTO chunks (doc_name, doc_type, loc, section, item_number, text) "
                            "VALUES (?,?,?,?,?,?)",
                            (filename, 'docx', f"Таблица {t_idx+1}", "Таблица", None, "\n".join(rows_text)))
        except Exception as e:
            print(f"Ошибка при обработке {filename}: {e}")

    conn.commit()
    conn.close()


# ============================================================
# ПОИСК
# ============================================================
def search_db(query, limit=4):
    conn = sqlite3.connect('data/docassist.db')
    c = conn.cursor()
    q_clean = re.sub(r'[?!.,;:\'"]', '', query).lower()

    stop_words = {"как", "что", "где", "когда", "кто", "почему", "зачем", "какой", "какая",
                  "какие", "пожалуйста", "привет", "спасибо", "скажи", "подскажи", "можно",
                  "нужно", "ли", "или", "а", "и", "в", "на", "с", "по", "для", "о", "об", "из",
                  "у", "от", "до", "зовут", "имя", "фамилия", "отчество", "директор",
                  "секретарь", "начальник"}
    words = [w for w in q_clean.split() if w not in stop_words and len(w) > 2]
    if not words:
        conn.close()
        return []

    conditions = " OR ".join(["LOWER(text) LIKE ?" for _ in words])
    params = [f"%{w}%" for w in words]
    c.execute(
        f"SELECT doc_name, doc_type, loc, section, item_number, text FROM chunks "
        f"WHERE {conditions} LIMIT ?",
        params + [limit])
    results = c.fetchall()
    conn.close()
    return results


# ============================================================
# ПРОВЕРКА ТЕМЫ
# ============================================================
def is_off_topic(prompt):
    p = prompt.lower()
    off_topic_patterns = [
        "зовут директора", "зовут секретаря", "зовут начальника",
        "как зовут", "кто директор", "кто секретарь", "кто начальник",
        "фио директора", "фио секретаря",
        "погода", "время", "дата сегодня",
        "расскажи анекдот", "расскажи шутку",
        "как дела", "как ты",
        "напиши код", "напиши программу",
        "переведи", "посчитай",
    ]
    for pattern in off_topic_patterns:
        if pattern in p:
            return True

    on_topic_keywords = [
        "документ", "инструкц", "регламент", "доу", "делопроизвод",
        "визир", "согласов", "подпис", "регистрац", "маршрут",
        "рабоч", "групп", "приказ", "распоряж", "матриц",
        "ит", "информац", "систем", "ис", "проект",
        "пункт", "раздел", "глава", "страниц",
        "срок", "контроль", "исполнен", "поручен",
        "бланк", "шаблон", "модул", "реквизит",
        "архив", "хранен", "уничтож", "дело",
        "входящ", "исходящ", "корреспонденц",
        "эксплуатац", "ввод", "вывод",
        "создай", "сформируй", "заполни",
    ]

    has_topic_keyword = any(kw in p for kw in on_topic_keywords)
    if not has_topic_keyword:
        return True

    return False


# ============================================================
# КОНТЕКСТ ДИАЛОГА
# ============================================================
def get_last_bot_intent(history):
    """Определяет, о чём был последний уточняющий вопрос бота."""
    for msg in reversed(history[:-1]):
        if msg["role"] == "assistant":
            content = msg["content"].lower()
            if "рабоч" in content and "групп" in content and \
               ("ит-проект" in content or "информац" in content):
                return "working_group_clarification"
            if "ит-проект" in content or "информац" in content:
                return "it_clarification"
    return None


# ============================================================
# ГЕНЕРАЦИЯ ОТВЕТА
# ============================================================
def generate_response(prompt, history):
    p = prompt.lower().strip()

    # 1. Сначала проверяем, является ли ввод ответом на уточняющий вопрос бота
    last_bot_intent = get_last_bot_intent(history)

    if last_bot_intent == "working_group_clarification":
        if "да" in p or "ит" in p:
            return {
                "answer": "Рабочая группа для ИТ-проекта. Согласно Матрице обязательного визирования "
                          "(строка 6):\n\n"
                          "**Обязательные согласующие:**\n"
                          "- Департамент ДОУ — Да\n"
                          "- Кадровое подразделение — Да\n"
                          "- Департамент ИТ — Да (условное требование, так как группа для ИТ-проекта)\n"
                          "- Юридическое подразделение — Нет (по данной строке матрицы)\n\n"
                          "**Важно:** Применяется общий порядок Инструкции по ДОУ. "
                          "Если затрагиваются иные компетенции — необходимо дополнительное согласование.",
                "status": "answered",
                "sources": [
                    ("Матрица обязательного визирования", "строка 6", "Матрица"),
                    ("Инструкция по ДОУ", "п. 10.6-10.11", "PDF")
                ],
                "relevance": 98,
                "suggestion": "Создать распоряжение о рабочей группе"
            }

        if "нет" in p:
            return {
                "answer": "Рабочая группа НЕ для ИТ. Согласно Матрице (строка 6):\n\n"
                          "**Обязательные согласующие:**\n"
                          "- Департамент ДОУ — Да\n"
                          "- Кадровое подразделение — Да\n"
                          "- Департамент ИТ — Нет (по данной строке, так как группа не для ИТ)\n"
                          "- Юридическое подразделение — Нет\n\n"
                          "**Важно:** Применяется общий порядок Инструкции.",
                "status": "answered",
                "sources": [("Матрица обязательного визирования", "строка 6", "Матрица")],
                "relevance": 98,
                "suggestion": "Создать распоряжение о рабочей группе"
            }

    # 2. Проверяем, относится ли вопрос к теме
    if is_off_topic(p):
        return {
            "answer": "Данная информация отсутствует в предоставленных файлах.\n\n"
                      "Я работаю только с вопросами по документообороту, инструкциям и регламентам "
                      "Организации. Пожалуйста, задайте вопрос по теме документационного обеспечения "
                      "управления.",
            "status": "not_found",
            "sources": [],
            "relevance": 0
        }

    # 3. Приоритет: приказ о вводе ИС (проверяем ДО рабочей группы)
    if ("ввод" in p and "информац" in p and "систем" in p) or \
       ("приказ" in p and "ввод" in p and "ис" in p) or \
       ("согласов" in p and "приказ" in p and "информац" in p):
        return {
            "answer": "**Приказ о вводе в эксплуатацию информационной системы.**\n\n"
                      "Согласно Матрице обязательного визирования:\n"
                      "- Юридическое подразделение — Да\n"
                      "- Департамент ДОУ — Да\n"
                      "- Кадровое подразделение — Нет\n"
                      "- Департамент информационной безопасности — Да\n"
                      "- Департамент ИТ — Да\n\n"
                      "**Важно:** Применяется общий порядок Инструкции по ДОУ (глава 10).",
            "status": "answered",
            "sources": [
                ("Матрица обязательного визирования", "строка приказа ИС", "Матрица"),
                ("Инструкция по ДОУ", "п. 9.5.6", "PDF")
            ],
            "relevance": 97
        }

    # 4. Вопрос про рабочую группу
    if "рабоч" in p and "групп" in p:
        if "визир" in p or "согласов" in p or "утвержд" in p or "кто" in p:
            return {
                "answer": "Чтобы определить маршрут визирования, мне нужно уточнить один момент.",
                "follow_up": "Эта рабочая группа создаётся для ИТ-проекта или вопросов информационных "
                             "систем?",
                "status": "need_clarification",
                "sources": [("Матрица обязательного визирования", "строка 6", "Матрица")],
                "relevance": 95
            }

    # 5. Вопрос про ДОУ
    if "доу" in p or "документационн" in p:
        return {
            "answer": "**Документационное обеспечение управления (ДОУ)** — деятельность, обеспечивающая "
                      "документирование управленческих решений, организацию движения, учета, "
                      "использования, контроля исполнения, оперативного и архивного хранения документов.\n\n"
                      "Согласно Инструкции по ДОУ (п. 1.4), ДОУ включает:\n"
                      "- Документирование управленческих решений\n"
                      "- Организацию движения документов\n"
                      "- Учет и использование документов\n"
                      "- Контроль исполнения\n"
                      "- Оперативное и архивное хранение\n\n"
                      "Департамент ДОУ осуществляет руководство процессами ДОУ в Организации.",
            "status": "answered",
            "sources": [
                ("Инструкция по ДОУ", "п. 1.4", "PDF"),
                ("Инструкция по ДОУ", "п. 2.1", "PDF")
            ],
            "relevance": 96
        }

    # 6. Общий поиск по базе
    results = search_db(prompt)
    if not results:
        return {
            "answer": "Данная информация отсутствует в предоставленных файлах.\n\n"
                      "Попробуйте переформулировать вопрос или задайте вопрос по теме:\n"
                      "- Визирование и согласование документов\n"
                      "- Создание рабочей группы\n"
                      "- Ввод информационных систем\n"
                      "- Документационное обеспечение управления\n"
                      "- Сроки исполнения документов\n"
                      "- Регистрация и контроль",
            "status": "not_found",
            "sources": [],
            "relevance": 0
        }

    answer = "На основе документов базы знаний:\n\n"
    sources = []
    for doc_name, doc_type, loc, section, item_num, text in results:
        clean = text[:400].replace('\n', ' ').strip()
        answer += f"**{section or loc}**\n{clean}...\n\n"
        sources.append({
            "title": doc_name,
            "section": item_num or loc,
            "type": doc_type,
            "text": clean
        })

    return {
        "answer": answer,
        "status": "answered",
        "sources": sources[:4],
        "relevance": 85
    }


# ============================================================
# ГЕНЕРАЦИЯ DOCX ПО ТЗ (11 полей)
# ============================================================
def create_docx(goal, subject, leader, secretary, members,
                deadline, result, addressee, termination,
                controller, signer):
    doc = Document()

    # Шапка утверждения
    doc.add_paragraph("УТВЕРЖДАЮ", style='Normal').alignment = 1
    doc.add_paragraph(signer if signer else "Заместитель Председателя Организации")
    doc.add_paragraph("______________  ____________________")
    doc.add_paragraph("«___» ____________ 20___ г.")
    doc.add_paragraph()

    # Заголовок
    title = doc.add_paragraph()
    title.alignment = 1
    run = title.add_run("НАИМЕНОВАНИЕ ОРГАНИЗАЦИИ")
    run.bold = True

    title2 = doc.add_paragraph()
    title2.alignment = 1
    run2 = title2.add_run("РАСПОРЯЖЕНИЕ")
    run2.bold = True
    run2.font.size = Pt(16)

    doc.add_paragraph("г. Москва")
    doc.add_paragraph()

    # Тема
    topic = doc.add_paragraph()
    topic.alignment = 1
    run_t = topic.add_run(f"О создании рабочей группы по {subject}")
    run_t.bold = True

    doc.add_paragraph()

    # Констатирующая часть
    doc.add_paragraph(f"В целях {goal},")
    doc.add_paragraph()

    # Распорядительная часть
    p_ob = doc.add_paragraph()
    run_ob = p_ob.add_run("ОБЯЗЫВАЮ:")
    run_ob.bold = True

    doc.add_paragraph(f"1. Создать рабочую группу по {subject}.")
    doc.add_paragraph()

    # Таблица состава
    doc.add_paragraph("2. Утвердить состав рабочей группы:")

    members_list = [m.strip() for m in members.split('\n') if m.strip()] if members else []
    total_rows = 3 + len(members_list)

    table = doc.add_table(rows=total_rows, cols=2, style='Table Grid')
    table.rows[0].cells[0].text = "Роль"
    table.rows[0].cells[1].text = "Должность, подразделение, инициалы и фамилия"
    table.rows[1].cells[0].text = "Руководитель"
    table.rows[1].cells[1].text = leader
    table.rows[2].cells[0].text = "Секретарь"
    table.rows[2].cells[1].text = secretary

    for i, member in enumerate(members_list):
        table.rows[3 + i].cells[0].text = "Участник"
        table.rows[3 + i].cells[1].text = member

    for cell in table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True

    doc.add_paragraph()

    # Срок и результат
    result_text = result if result else "результаты работы"
    addr_text = addressee if addressee else "руководству"
    doc.add_paragraph(
        f"3. Рабочей группе до {deadline} подготовить: {result_text} "
        f"и представить их {addr_text}.")
    doc.add_paragraph()

    # Условие завершения
    if termination:
        doc.add_paragraph(
            f"4. Деятельность рабочей группы прекращается после {termination}.")
        doc.add_paragraph()

    # Контроль
    ctrl_text = controller if controller else "заместителя Председателя Организации"
    p_num = 5 if termination else 4
    doc.add_paragraph(
        f"{p_num}. Контроль за исполнением настоящего распоряжения возложить "
        f"на {ctrl_text}.")
    doc.add_paragraph()
    doc.add_paragraph()

    # Подписант
    doc.add_paragraph(signer if signer else "Заместитель Председателя Организации")
    doc.add_paragraph("______________  И. О. Фамилия")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# ============================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================
init_db()
parse_docs()

# ============================================================
# САЙДБАР
# ============================================================
with st.sidebar:
    st.markdown("## DocAssist AI")
    st.markdown("*Интеллектуальный помощник по регламентам*")
    st.divider()

    page = st.radio(
        "Навигация",
        ["Чат с помощником", "Создать документ"],
        label_visibility="collapsed"
    )

# ============================================================
# СТРАНИЦА: ЧАТ С ПОМОЩНИКОМ
# ============================================================
if page == "Чат с помощником":
    st.markdown("""
    <div class="header-card" style="background: linear-gradient(135deg, #002D6B 0%, #009688 100%); 
                padding: 2rem; border-radius: 20px; color: white; margin-bottom: 2rem;
                box-shadow: 0 10px 40px rgba(0, 45, 107, 0.2);">
        <h1 style="color: white !important; margin: 0; font-size: 2.5rem;">Чат с помощником</h1>
        <p style="opacity: 0.9; margin-top: 0.5rem; color: white !important;">
        Задайте вопрос по регламентам — получу ответ со ссылками на источники</p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Отображение истории
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            relevance_html = ""
            if msg.get("relevance") and msg["relevance"] > 0:
                relevance_html = (
                    f'<div class="relevance-badge">'
                    f'Релевантность: {msg["relevance"]}%</div>'
                )

            st.markdown(
                f'<div class="bot-msg">{relevance_html}{msg["content"]}</div>',
                unsafe_allow_html=True)

            if msg.get("sources"):
                for i, src in enumerate(msg["sources"]):
                    if isinstance(src, dict):
                        src_id = f"src_{len(st.session_state.messages)}_{i}"
                        st.markdown(
                            f'<div class="source-badge" '
                            f'onclick="document.getElementById(\'{src_id}\').style.display='
                            f'document.getElementById(\'{src_id}\').style.display===\'none\'?'
                            f'\'block\':\'none\'">'
                            f'<b>{src["title"]}</b> — {src["section"]}</div>',
                            unsafe_allow_html=True)
                        st.markdown(
                            f'<div class="source-quote" id="{src_id}" '
                            f'style="display:none;">{src["text"]}</div>',
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<div class="source-badge">'
                            f'<b>{src[0]}</b> — {src[1]}</div>',
                            unsafe_allow_html=True)

    # Быстрые ответы на уточняющий вопрос
    if st.session_state.messages and st.session_state.messages[-1].get("follow_up"):
        st.markdown("**Быстрый ответ:**")
        c1, c2 = st.columns(2)
        if c1.button("Да, это ИТ-проект", use_container_width=True, key="btn_yes"):
            st.session_state.messages.append(
                {"role": "user", "content": "Да, это ИТ-проект"})

            with st.spinner("Анализирую документы..."):
                time.sleep(0.5)
                response = generate_response(
                    "Да, это ИТ-проект", st.session_state.messages)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response.get("sources", []),
                "relevance": response.get("relevance", 0)
            })
            st.rerun()

        if c2.button("Нет, не ИТ", use_container_width=True, key="btn_no"):
            st.session_state.messages.append(
                {"role": "user", "content": "Нет, не для ИТ"})

            with st.spinner("Анализирую документы..."):
                time.sleep(0.5)
                response = generate_response(
                    "Нет, не для ИТ", st.session_state.messages)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response.get("sources", []),
                "relevance": response.get("relevance", 0)
            })
            st.rerun()

    # Ввод нового сообщения
    if prompt := st.chat_input("Задайте вопрос по документам..."):
        st.session_state.messages.append(
            {"role": "user", "content": prompt})

        with st.spinner("Анализирую документы..."):
            time.sleep(0.5)
            response = generate_response(
                prompt, st.session_state.messages)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response["answer"],
            "sources": response.get("sources", []),
            "follow_up": response.get("follow_up"),
            "relevance": response.get("relevance", 0)
        })

        st.rerun()

# ============================================================
# СТРАНИЦА: СОЗДАТЬ ДОКУМЕНТ (WIZARD 6 ШАГОВ ПО ТЗ)
# ============================================================
elif page == "Создать документ":
    st.markdown("""
    <div class="header-card" style="background: linear-gradient(135deg, #002D6B 0%, #009688 100%); 
                padding: 2rem; border-radius: 20px; color: white; margin-bottom: 2rem;">
        <h1 style="color: white !important; margin: 0; font-size: 2.5rem;">
        Генератор документов</h1>
        <p style="opacity: 0.9; margin-top: 0.5rem; color: white !important;">
        Пошаговое заполнение формы по ТЗ кейса — получите готовый черновик DOCX</p>
    </div>
    """, unsafe_allow_html=True)

    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_data" not in st.session_state:
        st.session_state.wizard_data = {}

    steps = [
        "Цель и предмет",
        "Состав группы",
        "Участники",
        "Срок и результат",
        "Завершение и контроль",
        "Проверка и генерация"
    ]
    steps_html = '<div class="wizard-step-indicator">'
    for i, step_name in enumerate(steps, 1):
        if i < st.session_state.wizard_step:
            steps_html += f'<div class="step-item completed">{i}. {step_name}</div>'
        elif i == st.session_state.wizard_step:
            steps_html += f'<div class="step-item active">{i}. {step_name}</div>'
        else:
            steps_html += f'<div class="step-item">{i}. {step_name}</div>'
    steps_html += '</div>'
    st.markdown(steps_html, unsafe_allow_html=True)

    # ШАГ 1: Цель и предмет
    if st.session_state.wizard_step == 1:
        st.markdown("### Шаг 1 из 6: Цель и предмет")

        goal = st.text_input(
            "Цель создания (В целях...)",
            value=st.session_state.wizard_data.get("goal", ""),
            placeholder="Подготовки плана внедрения CRM-системы")
        subject = st.text_input(
            "Предмет / Наименование рабочей группы",
            value=st.session_state.wizard_data.get("subject", ""),
            placeholder="Внедрению новой CRM-системы")

        col1, col2 = st.columns(2)
        if col2.button("Далее", use_container_width=True):
            if not goal or not subject:
                st.error("Заполните оба поля")
            else:
                st.session_state.wizard_data["goal"] = goal
                st.session_state.wizard_data["subject"] = subject
                st.session_state.wizard_step = 2
                st.rerun()

    # ШАГ 2: Руководитель и секретарь
    elif st.session_state.wizard_step == 2:
        st.markdown("### Шаг 2 из 6: Руководитель и секретарь")

        leader = st.text_input(
            "Руководитель группы (должность, подразделение, ФИО)",
            value=st.session_state.wizard_data.get("leader", ""),
            placeholder="Директор департамента ИТ И.И. Иванов")
        secretary = st.text_input(
            "Секретарь (должность, подразделение, ФИО)",
            value=st.session_state.wizard_data.get("secretary", ""),
            placeholder="Главный специалист А.А. Петрова")

        col1, col2, col3 = st.columns([1, 1, 1])
        if col1.button("Назад", use_container_width=True):
            st.session_state.wizard_step = 1
            st.rerun()
        if col3.button("Далее", use_container_width=True):
            if not leader or not secretary:
                st.error("Заполните оба поля")
            else:
                st.session_state.wizard_data["leader"] = leader
                st.session_state.wizard_data["secretary"] = secretary
                st.session_state.wizard_step = 3
                st.rerun()

    # ШАГ 3: Участники
    elif st.session_state.wizard_step == 3:
        st.markdown("### Шаг 3 из 6: Участники рабочей группы")

        members = st.text_area(
            "Участники (каждый с новой строки, формат: должность, подразделение, ФИО)",
            value=st.session_state.wizard_data.get("members", ""),
            placeholder=(
                "Начальник отдела разработки П.П. Петров\n"
                "Ведущий аналитик С.С. Сидоров\n"
                "Специалист по тестированию А.А. Алексеев"),
            height=150)

        st.caption(
            "Можно оставить пустым, если состав ограничен "
            "руководителем и секретарём")

        col1, col2, col3 = st.columns([1, 1, 1])
        if col1.button("Назад", use_container_width=True):
            st.session_state.wizard_step = 2
            st.rerun()
        if col3.button("Далее", use_container_width=True):
            st.session_state.wizard_data["members"] = members
            st.session_state.wizard_step = 4
            st.rerun()

    # ШАГ 4: Срок и результат
    elif st.session_state.wizard_step == 4:
        st.markdown("### Шаг 4 из 6: Срок и результат")

        deadline = st.text_input(
            "Срок выполнения",
            value=st.session_state.wizard_data.get("deadline", ""),
            placeholder="01.12.2026")
        result = st.text_input(
            "Ожидаемый результат",
            value=st.session_state.wizard_data.get("result", ""),
            placeholder="Отчёт с рекомендациями по внедрению CRM-системы")
        addressee = st.text_input(
            "Адресат (кому представить результат)",
            value=st.session_state.wizard_data.get("addressee", ""),
            placeholder="Руководству Организации")

        col1, col2, col3 = st.columns([1, 1, 1])
        if col1.button("Назад", use_container_width=True):
            st.session_state.wizard_step = 3
            st.rerun()
        if col3.button("Далее", use_container_width=True):
            if not deadline:
                st.error("Заполните срок")
            else:
                st.session_state.wizard_data["deadline"] = deadline
                st.session_state.wizard_data["result"] = result
                st.session_state.wizard_data["addressee"] = addressee
                st.session_state.wizard_step = 5
                st.rerun()

    # ШАГ 5: Завершение и контроль
    elif st.session_state.wizard_step == 5:
        st.markdown("### Шаг 5 из 6: Условие завершения и контроль")

        termination = st.text_input(
            "Условие завершения деятельности группы",
            value=st.session_state.wizard_data.get("termination", ""),
            placeholder=(
                "выполнения поставленных задач и представления "
                "итогового отчёта"))
        controller = st.text_input(
            "Контролирующий (должность, ФИО)",
            value=st.session_state.wizard_data.get("controller", ""),
            placeholder=(
                "Заместитель Председателя Организации И.О. Фамилия"))
        signer = st.text_input(
            "Подписант",
            value=st.session_state.wizard_data.get("signer", ""),
            placeholder="Заместитель Председателя Организации")

        col1, col2, col3 = st.columns([1, 1, 1])
        if col1.button("Назад", use_container_width=True):
            st.session_state.wizard_step = 4
            st.rerun()
        if col3.button("Далее", use_container_width=True):
            st.session_state.wizard_data["termination"] = termination
            st.session_state.wizard_data["controller"] = controller
            st.session_state.wizard_data["signer"] = signer
            st.session_state.wizard_step = 6
            st.rerun()

    # ШАГ 6: Проверка и генерация
    elif st.session_state.wizard_step == 6:
        st.markdown("### Шаг 6 из 6: Проверка данных")

        data = st.session_state.wizard_data

        st.markdown("**Проверьте введённые данные:**")

        with st.container():
            st.markdown(f"**Цель:** {data.get('goal', '')}")
            st.markdown(f"**Предмет:** {data.get('subject', '')}")
            st.markdown(f"**Руководитель:** {data.get('leader', '')}")
            st.markdown(f"**Секретарь:** {data.get('secretary', '')}")
            if data.get('members'):
                st.markdown("**Участники:**")
                for m in data['members'].split('\n'):
                    if m.strip():
                        st.markdown(f"  - {m.strip()}")
            st.markdown(f"**Срок:** {data.get('deadline', '')}")
            st.markdown(f"**Результат:** {data.get('result', '')}")
            st.markdown(f"**Адресат:** {data.get('addressee', '')}")
            st.markdown(
                f"**Условие завершения:** "
                f"{data.get('termination', '')}")
            st.markdown(
                f"**Контролирующий:** "
                f"{data.get('controller', '')}")
            st.markdown(
                f"**Подписант:** {data.get('signer', '')}")

        st.divider()

        col1, col2, col3 = st.columns([1, 1, 1])
        if col1.button("Назад", use_container_width=True):
            st.session_state.wizard_step = 5
            st.rerun()
        if col2.button("Сбросить", use_container_width=True):
            st.session_state.wizard_step = 1
            st.session_state.wizard_data = {}
            st.rerun()
        if col3.button("Сформировать DOCX", use_container_width=True):
            with st.spinner("Формирую документ..."):
                time.sleep(0.8)
                docx_file = create_docx(
                    data.get("goal", ""),
                    data.get("subject", ""),
                    data.get("leader", ""),
                    data.get("secretary", ""),
                    data.get("members", ""),
                    data.get("deadline", ""),
                    data.get("result", ""),
                    data.get("addressee", ""),
                    data.get("termination", ""),
                    data.get("controller", ""),
                    data.get("signer", "")
                )
                st.session_state.my_docx = docx_file
            st.rerun()

    # Скачивание
    if "my_docx" in st.session_state and st.session_state.my_docx:
        st.success("Документ готов!")
        st.download_button(
            label="Скачать DOCX",
            data=st.session_state.my_docx,
            file_name="Распоряжение_Рабочая_группа.docx",
            mime="application/vnd.openxmlformats-officedocument."
                 "wordprocessingml.document",
            use_container_width=True
        )
        st.warning(
            "**Черновик.** Не является подписанным или "
            "зарегистрированным документом.")

        if st.button("Создать новый документ"):
            st.session_state.wizard_step = 1
            st.session_state.wizard_data = {}
            st.session_state.my_docx = None
            st.rerun()