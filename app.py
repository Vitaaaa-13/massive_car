"""DocAssist AI: source-backed questions and original modular document drafts."""
import hashlib
import hmac
import io
import json
import logging
import os

import streamlit as st
from docx import Document

import docassist as core
import templates

st.set_page_config(page_title="DocAssist AI", layout="wide", page_icon="📄")


@st.cache_resource
def initialize():
    core.seed_documents()
    return True


initialize()
if "session_id" not in st.session_state:
    st.session_state.session_id = core.new_session()
if "theme" not in st.session_state:
    saved_theme = st.query_params.get("theme", "Системная")
    st.session_state.theme = saved_theme if saved_theme in ("Системная", "Светлая", "Тёмная") else "Системная"

theme = st.session_state.theme
light_css = "--background:#f4f6f9;--surface:#fff;--text:#152338;--muted:#607086;--line:#dbe2eb;"
dark_css = "--background:#141a23;--surface:#1e2733;--text:#edf3fc;--muted:#abb9ca;--line:#39485a;"
css = f"""<style>
:root {{{dark_css if theme == 'Тёмная' else light_css}}}
{':root {' + dark_css + '}' if theme == 'Системная' else ''}
@media (prefers-color-scheme: light) {{ {':root {' + light_css + '}' if theme == 'Системная' else ''} }}
.stApp, [data-testid="stSidebar"] {{background:var(--background);color:var(--text)}}
[data-testid="stMainBlockContainer"] {{max-width:1050px;padding-top:2rem}}
[data-testid="stAppViewContainer"] :is(h1,h2,h3,p,label,span,li),
[data-testid="stSidebar"] :is(h1,h2,h3,p,label,span,li) {{color:var(--text)!important}}
[data-testid="stForm"] {{background:var(--surface)!important;border-color:var(--line)!important}}
[data-baseweb="input"], [data-baseweb="select"] > div, textarea,
[data-testid="stChatInput"] {{background:var(--surface)!important;color:var(--text)!important;border-color:var(--line)!important}}
[data-baseweb="input"] input, [data-baseweb="select"] input, textarea {{color:var(--text)!important}}
[data-testid="stChatMessage"] {{background:var(--surface);border:1px solid var(--line);border-radius:12px}}
[data-testid="stHeader"], [data-testid="stBottom"] {{background:var(--background)!important}}
[data-testid="stBottom"] > div {{background:var(--background)!important}}
.stButton button, .stDownloadButton button {{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:8px}}
.stButton button *, .stDownloadButton button * {{color:var(--text)!important}}
.stButton button[kind="primary"] {{background:#235bb4!important;color:#fff!important}}
.stButton button[kind="primary"] * {{color:#fff!important}}
</style>"""
st.markdown(css, unsafe_allow_html=True)


def is_admin():
    return bool(st.session_state.get("admin"))


def check_password(password):
    stored = os.getenv("DOCASSIST_ADMIN_PASSWORD_HASH", "")
    if not stored:
        return False
    try:
        salt, expected = stored.split(":", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 250_000).hex()
        return hmac.compare_digest(actual, expected)
    except ValueError:
        return False


def admin_access_panel():
    if is_admin():
        st.success("Режим администратора")
        if st.button("Выйти из режима администратора"):
            st.session_state.admin = False
            st.rerun()
    else:
        with st.expander("Управление документами"):
            with st.form("admin_login"):
                password = st.text_input("Пароль администратора", type="password")
                if st.form_submit_button("Войти"):
                    if check_password(password):
                        st.session_state.admin = True
                        st.rerun()
                    else:
                        st.error("Неверный пароль или вход не настроен")


with st.sidebar:
    st.title("DocAssist AI")
    st.caption("Помощник по внутренним документам")
    page = st.radio("Раздел", ["Чат", "Документы", "Шаблоны", "Проверка черновика", "О проекте"])
    st.selectbox("Тема", ["Системная", "Светлая", "Тёмная"], key="theme")
    if st.query_params.get("theme") != st.session_state.theme:
        st.query_params["theme"] = st.session_state.theme


if page == "Чат":
    st.title("Вопросы по документам")
    st.caption("GigaChat отвечает по найденным фрагментам активных редакций.")
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Новый диалог"):
            st.session_state.session_id = core.new_session()
            st.rerun()
    with col2:
        available = core.sessions()
        selected = st.selectbox("Диалог", [x["id"] for x in available],
            index=next((i for i, x in enumerate(available) if x["id"] == st.session_state.session_id), 0),
            format_func=lambda x: x[:8])
        if selected != st.session_state.session_id:
            st.session_state.session_id = selected
            st.rerun()
    history = core.messages(st.session_state.session_id)
    if history:
        transcript = "# Диалог DocAssist AI\n\n" + "\n\n".join(
            f"## {'Вы' if message['role'] == 'user' else 'DocAssist AI'}\n\n{message['content']}"
            for message in history)
        st.download_button("Скачать диалог", transcript,
            file_name=f"docassist-{st.session_state.session_id[:8]}.md", mime="text/markdown")
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Спросите о требованиях и документах")
    if prompt:
        core.add_message(st.session_state.session_id, "user", prompt)
        with st.spinner("Ищу источники и формирую ответ..."):
            response = core.answer(prompt, history)
        core.add_message(st.session_state.session_id, "assistant", response["answer"],
                         [x["revision_id"] for x in response["sources"]],
                         [x["id"] for x in response["sources"]])
        st.rerun()
    if history and history[-1]["role"] == "assistant":
        used = json.loads(history[-1]["source_ids"])
        if used:
            st.subheader("Источники последнего ответа")
            with core.connect() as db:
                rows = db.execute("""SELECT f.text,f.locator,r.number,d.title FROM fragments f
                    JOIN revisions r ON r.id=f.revision_id JOIN documents d ON d.id=r.document_id
                    WHERE f.id IN (%s) LIMIT 6""" % ",".join("?" for _ in used), used).fetchall()
            for row in rows:
                with st.expander(f"{row['title']} · редакция {row['number']} · {row['locator']}"):
                    st.write(row["text"])

elif page == "Документы":
    st.title("Документы и редакции")
    admin_access_panel()
    filter_text = st.text_input("Найти документ", placeholder="Название или статус")
    visible_docs = [item for item in core.documents() if filter_text.casefold() in
                    f"{item['title']} {item['status']}".casefold()]
    if not visible_docs:
        st.info("По этому запросу документов нет")
    for item in visible_docs:
        with st.expander(f"{item['title']} · редакция {item['number']} · {item['status']}"):
            st.caption(f"Индексировано: {item['indexed_at']}")
            for revision in core.revisions(item["id"]):
                col1, col2 = st.columns([4, 1])
                col1.write(f"Редакция {revision['number']} · SHA256 {revision['sha256'][:12]} · {revision['status']}")
                if is_admin() and revision["id"] != item["active_revision"]:
                    if col2.button("Активировать", key=f"act-{revision['id']}"):
                        core.activate(item["id"], revision["id"])
                        st.rerun()
    if is_admin():
        st.subheader("Загрузить документ")
        uploaded = st.file_uploader("PDF или DOCX", type=["pdf", "docx"])
        existing = st.selectbox("Редакция", ["Новый документ"] + [x["title"] for x in core.documents()])
        if uploaded and st.button("Индексировать", type="primary"):
            target_id = next((x["id"] for x in core.documents() if x["title"] == existing), None)
            try:
                revision_id = core.ingest(uploaded.getvalue(), uploaded.name, target_id)
                st.success(f"Редакция {revision_id} индексирована и активирована")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    st.subheader("Маршрут визирования")
    kind = st.selectbox("Вид", ["Рабочая группа", "Приказ о вводе ИС"])
    is_it = st.checkbox("Связан с ИТ-проектом", value=True, disabled=kind != "Рабочая группа")
    route = core.approval_route("working_group" if kind == "Рабочая группа" else "information_system", is_it)
    if not route:
        st.warning("Маршрут недоступен: проверьте исходный файл активной матрицы.")
    for step in route:
        st.write(f"**{step['department']}** — {step['reason']}")
    st.caption("Другие согласующие могут требоваться по общему порядку и затронутым компетенциям.")

elif page == "Шаблоны":
    st.title("Оригинальные модульные документы")
    items = templates.catalog()
    choice = st.selectbox("Модуль", [x["id"] for x in items], format_func=lambda x: next(i["title"] for i in items if i["id"] == x))
    st.caption("Черновик создаётся из исходного DOCX. Дата, номер и блок электронной подписи сохраняются.")
    schema = templates.fields_for(choice)
    with st.form("template_form"):
        values = {}
        for key, description in schema.items():
            short_label = description.split(".", 1)[0].strip()
            values[key] = st.text_input(f"{key}. {short_label}", key=f"{choice}-{key}", help=description)
        if "рабоч" in choice:
            values["3_leader"] = st.text_input("Руководитель группы")
            values["3_secretary"] = st.text_input("Секретарь группы")
            values["4_action"] = st.text_input("Действие к сроку", value="подготовить результат")
        submitted = st.form_submit_button("Создать DOCX", type="primary")
    if submitted:
        st.session_state.pop("generated_docx", None)
        st.session_state.pop("generated_docx_name", None)
        st.session_state.pop("generated_template_id", None)
        try:
            st.session_state.generated_docx = templates.create_draft(choice, values)
            st.session_state.generated_docx_name = choice.replace("Модуль_", "Черновик_")
            st.session_state.generated_template_id = choice
            st.success("Черновик создан из исходного модуля")
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            logging.exception("Failed to generate DOCX from template %s", choice)
            st.error("Не удалось создать DOCX. Проверьте данные и попробуйте ещё раз.")
    if st.session_state.get("generated_docx") and st.session_state.get("generated_template_id") == choice:
        st.download_button("Скачать DOCX", st.session_state.generated_docx,
            st.session_state.generated_docx_name,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif page == "Проверка черновика":
    st.title("Проверка черновика")
    uploaded = st.file_uploader("Загрузите DOCX", type=["docx"])
    if uploaded:
        draft = Document(io.BytesIO(uploaded.getvalue()))
        content = "\n".join(p.text for p in draft.paragraphs)
        issues = []
        if "___" in content:
            issues.append("Есть незаполненные поля")
        if "Примечания по заполнению" in content:
            issues.append("Остались служебные пояснения модуля")
        if not any(x in content for x in ("ПРИКАЗ", "РАСПОРЯЖЕНИЕ")):
            issues.append("Не определён тип распорядительного документа")
        if issues:
            for issue in issues:
                st.warning(issue)
        else:
            st.success("Очевидных незаполненных реквизитов не найдено")
        st.caption("Автоматическая проверка реквизитов; юридическую экспертизу не заменяет.")

else:
    st.title("О проекте")
    st.write("PDF и DOCX индексируются по фрагментам. Полнотекстовый поиск находит кандидатов, GigaChat формирует ответ по найденному контексту. Ссылки на отсутствующие фрагменты отбрасываются.")
    st.write("**Модель:**", os.getenv("GIGACHAT_MODEL", "GigaChat-3-Lightning"))
    st.write("**GigaChat:**", "ключ настроен" if os.getenv("GIGACHAT_AUTH_KEY") else "ключ не настроен")
    st.caption("Демонстрация на синтетических документах. Для реальных банковских данных нужна отдельная оценка защиты и политики передачи данных.")
