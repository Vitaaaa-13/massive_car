import io

from docx import Document
from streamlit.testing.v1 import AppTest

import docassist as core
import templates


def test_template_form_creates_docx_and_handles_missing_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "DATA", tmp_path)
    monkeypatch.setattr(core, "DB", tmp_path / "test.db")
    monkeypatch.setattr(core, "FILES", tmp_path / "uploads")

    app = AppTest.from_file("app.py").run()
    app.sidebar.radio[0].set_value("Шаблоны").run()
    assert not app.exception

    app.button(key="FormSubmitter:template_form-Создать DOCX").click().run()
    assert not app.exception
    assert any("Заполните обязательные поля" in error.value for error in app.error)
    assert "generated_docx" not in app.session_state

    item = templates.catalog()[0]
    for key in item["notes"]:
        app.text_input(key=f"{item['id']}-{key}").set_value(f"Тестовое значение {key}")
    app.button(key="FormSubmitter:template_form-Создать DOCX").click().run()

    assert not app.exception
    assert any("Черновик создан" in success.value for success in app.success)
    draft = Document(io.BytesIO(app.session_state.generated_docx))
    assert draft.paragraphs
    assert app.session_state.generated_docx_name.endswith(".docx")

    app.text_input(key=f"{item['id']}-{next(iter(item['notes']))}").set_value("")
    app.button(key="FormSubmitter:template_form-Создать DOCX").click().run()
    assert not app.exception
    assert "generated_docx" not in app.session_state
