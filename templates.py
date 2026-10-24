"""Fill original modular DOCX files while retaining their document structure."""
from __future__ import annotations

import io
import re
from pathlib import Path

from docx import Document

SEED = Path("data/seed")
NOTE = re.compile(r"\[(\d+)\]")
BLANK = re.compile(r"«?_{3,}»?(?:\s+_{3,})*(?:\s+20_{3}\s*г\.)?")


def catalog():
    result = []
    for path in sorted(SEED.glob("Модуль*.docx")):
        doc = Document(path)
        title = next((p.text for p in doc.paragraphs if p.text.startswith(("О ", "Об "))), path.stem)
        title = re.sub(r"\[[^]]+\]|_{3,}", "", title.splitlines()[0])
        title = re.sub(r"\s+", " ", title).strip(" /- ")
        notes = {}
        in_notes = False
        for p in doc.paragraphs:
            value = p.text.strip()
            if value.startswith("Примечания по заполнению"):
                in_notes = True
            elif in_notes:
                match = re.match(r"^(\d+)\.\s+(.+)", value)
                if match:
                    notes[match.group(1)] = match.group(2)
        result.append({"id": path.name, "title": title, "notes": notes})
    return result


def template_path(template_id):
    path = SEED / Path(template_id).name
    if not path.name.startswith("Модуль") or path.suffix != ".docx" or not path.is_file():
        raise ValueError("Модуль не найден")
    return path


def fields_for(template_id):
    return next(item["notes"] for item in catalog() if item["id"] == template_id)


def validate(template_id, values):
    notes = fields_for(template_id)
    optional = {"5", "9", "2"} if "проектного_комитета" in template_id else {"5"} if "ответственных" in template_id else set()
    missing = [key for key in notes if key not in optional and not str(values.get(key, "")).strip()]
    return missing


def _set_text(paragraph, value):
    # Keep the paragraph and its properties. Unchanged runs retain their style.
    if paragraph.runs:
        paragraph.runs[0].text = value
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(value)


def _fill_segment(segment, value):
    if not value:
        return segment
    result = BLANK.sub(value, segment)
    if result == segment and "И. О. Фамилия" in segment:
        result = segment.replace("И. О. Фамилия", value)
    return result


def _fill_text(text, values):
    cursor = 0
    output = ""
    for match in NOTE.finditer(text):
        number = match.group(1)
        output += _fill_segment(text[cursor:match.start()], str(values.get(number, "")))
        cursor = match.end()
    output += text[cursor:]
    return output


def _remove_paragraph(paragraph):
    element = paragraph._element
    element.getparent().remove(element)


def create_draft(template_id, values, allow_incomplete=False):
    missing = validate(template_id, values)
    if missing and not allow_incomplete:
        raise ValueError("Не заполнены поля: " + ", ".join(missing))
    document = Document(template_path(template_id))
    note_start = next((i for i, p in enumerate(document.paragraphs)
                       if p.text.strip().startswith("Примечания по заполнению")), len(document.paragraphs))
    is_group = "рабочей_группы" in template_id or "рабочей_группы" in template_id
    for index, paragraph in enumerate(list(document.paragraphs)):
        if index >= note_start:
            _remove_paragraph(paragraph)
            continue
        old = paragraph.text
        if index == 0 and old.strip() == "МОДУЛЬНЫЙ ДОКУМЕНТ":
            _remove_paragraph(paragraph)
            continue
        if is_group:
            group_lines = {
                5: f"О создании рабочей группы по {values.get('2', '')}",
                6: f"В целях {values.get('1', '')},",
                8: f"1. Создать рабочую группу по {values.get('2', '')} (далее - Рабочая группа) в составе:",
                9: f"2. Рабочей группе до {values.get('4', '')} {values.get('4_action', 'выполнить поставленные задачи')} и представить {values.get('5', '')}.",
                12: f"5. Рабочая группа прекращает деятельность после {values.get('6', '')}.",
                13: f"6. Контроль за исполнением настоящего распоряжения возложить на {values.get('7', '')}.",
            }
            if index in group_lines:
                _set_text(paragraph, group_lines[index])
                continue
        new = _fill_text(old, values)
        if new != old:
            _set_text(paragraph, new)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    old = paragraph.text
                    new = _fill_text(old, values)
                    if new != old:
                        _set_text(paragraph, new)
    if is_group:
        composition = document.tables[2]
        for row, key in ((1, "3_leader"), (2, "3_secretary"), (3, "3")):
            _set_text(composition.rows[row].cells[1].paragraphs[0], str(values.get(key, values.get("3", ""))))
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()
