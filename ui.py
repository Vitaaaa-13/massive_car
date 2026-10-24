"""Small, shared presentation helpers for both DocAssist themes."""
from html import escape


LIGHT = "--background:#f3f6fb;--sidebar:#eaf0f8;--surface:#fff;--surface-alt:#f8faff;--text:#18253c;--muted:#60718a;--line:#d8e2ee;--accent:#3558d4;--accent-soft:#e9eeff;--glow:rgba(91,132,235,.15);--shadow:0 12px 35px rgba(32,55,92,.07);"
DARK = "--background:#101722;--sidebar:#111c2b;--surface:#1a2636;--surface-alt:#202f43;--text:#f0f5ff;--muted:#aabbd0;--line:#32445a;--accent:#91aaff;--accent-soft:#263a68;--glow:rgba(64,99,184,.2);--shadow:0 14px 38px rgba(0,0,0,.18);"

CSS = """
.stApp {background:radial-gradient(circle at 70% -18%,var(--glow),transparent 42%),var(--background);color:var(--text)}
[data-testid="stSidebar"] {background:var(--sidebar)!important;border-right:1px solid var(--line)}
[data-testid="stMainBlockContainer"] {max-width:1180px;padding-top:2.1rem;padding-bottom:8rem}
[data-testid="stAppViewContainer"] :is(h1,h2,h3,p,label,span,li),
[data-testid="stSidebar"] :is(h1,h2,h3,p,label,span,li) {color:var(--text)}
[data-testid="stCaptionContainer"] p {color:var(--muted)!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {padding:.48rem .68rem;border-radius:10px;transition:background .15s ease}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {display:none}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover {background:var(--surface-alt)}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {background:var(--accent-soft);font-weight:650}
[data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {background:var(--surface)!important;border-color:var(--line)!important;border-radius:18px!important;box-shadow:var(--shadow)}
[data-testid="stExpander"] {background:var(--surface)!important;border:1px solid var(--line)!important;border-radius:12px!important}
[data-baseweb="input"], [data-baseweb="select"] > div, textarea,
[data-testid="stChatInput"] {background:var(--surface)!important;color:var(--text)!important;border-color:var(--line)!important;border-radius:11px!important}
[data-baseweb="input"] input, [data-baseweb="select"] input, textarea {color:var(--text)!important}
[data-baseweb="popover"], [data-baseweb="menu"] {background:var(--surface)!important;color:var(--text)!important}
[data-testid="stChatMessage"] {background:var(--surface-alt)!important;border:1px solid var(--line);border-radius:14px;padding:1rem 1.15rem;box-shadow:none}
[data-testid="stHeader"] {background:transparent!important}
[data-testid="stBottom"] {background:linear-gradient(transparent,var(--background) 28%)!important;padding-top:.6rem}
[data-testid="stBottom"] > div {background:transparent!important}
[data-testid="stChatInput"] {box-shadow:0 9px 28px rgba(0,0,0,.13)!important}
.stButton button, .stDownloadButton button {background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:10px;min-height:2.6rem;transition:border-color .15s ease,transform .15s ease}
.stButton button:hover, .stDownloadButton button:hover {border-color:var(--accent)!important;transform:translateY(-1px)}
.stButton button *, .stDownloadButton button * {color:var(--text)!important}
.stButton button[kind="primary"] {background:var(--accent)!important;border-color:var(--accent)!important;color:#fff!important}
.stButton button[kind="primary"] * {color:#fff!important}
.brand {display:flex;align-items:center;gap:.75rem;margin:.2rem 0 .45rem}
.brand-mark {display:grid;place-items:center;width:2.45rem;height:2.45rem;border-radius:12px;background:linear-gradient(135deg,#5275ed,#8d63db);color:#fff;font-weight:800;font-size:1.25rem;box-shadow:0 8px 18px rgba(69,92,193,.25)}
.brand-name {font-size:1.23rem;font-weight:760;letter-spacing:-.035em;color:var(--text)}
.brand-note {color:var(--muted);font-size:.79rem;line-height:1.3}
.page-hero {padding:1.35rem 1.55rem 1.45rem;border:1px solid var(--line);border-radius:20px;background:linear-gradient(115deg,var(--surface),var(--surface-alt));box-shadow:var(--shadow);margin-bottom:1.15rem}
.eyebrow {color:var(--accent);font-size:.69rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.48rem}
.page-hero h1 {color:var(--text);font-size:2.15rem;line-height:1.12;margin:.1rem 0 .52rem;letter-spacing:-.035em}
.page-hero p {color:var(--muted)!important;font-size:.93rem;margin:0;line-height:1.45}
.hero-meta {display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1rem}
.hero-chip {display:inline-flex;align-items:center;gap:.35rem;padding:.32rem .65rem;border-radius:999px;background:var(--accent-soft);color:var(--accent)!important;font-size:.73rem;font-weight:700}
.section-heading {display:flex;align-items:center;gap:.7rem;margin:1.35rem 0 .75rem}
.section-index {display:grid;place-items:center;width:2rem;height:2rem;border-radius:9px;background:var(--accent-soft);color:var(--accent)!important;font-size:.7rem;font-weight:800}
.section-heading h2 {margin:0;color:var(--text);font-size:1.3rem;line-height:1.2}
.section-heading p {margin:.12rem 0 0;color:var(--muted)!important;font-size:.8rem}
.empty-chat {text-align:center;padding:2.3rem 1rem;color:var(--muted)}
.empty-chat strong {display:block;color:var(--text);font-size:1.1rem;margin-bottom:.25rem}
.small-label {color:var(--muted);font-size:.7rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase;margin:1.05rem 0 .55rem}
@media (max-width:700px) {[data-testid="stMainBlockContainer"] {padding-top:1rem}.page-hero {padding:1rem}.page-hero h1 {font-size:1.7rem}}
"""


def inject_theme(st, theme):
    if theme == "Системная":
        palette = f":root {{{LIGHT}}} @media (prefers-color-scheme: dark) {{ :root {{{DARK}}} }}"
    else:
        palette = f":root {{{LIGHT if theme == 'Светлая' else DARK}}}"
    st.markdown("<style>" + palette + CSS + "</style>", unsafe_allow_html=True)


def sidebar_brand(st):
    st.markdown(
        '<div class="brand"><div class="brand-mark">D</div><div>'
        '<div class="brand-name">DocAssist AI</div>'
        '<div class="brand-note">Навигатор по документам</div></div></div>',
        unsafe_allow_html=True,
    )


def page_header(st, kicker, title, description, chips=()):
    chips_html = "".join(f'<span class="hero-chip">{escape(chip)}</span>' for chip in chips)
    st.markdown(
        f'<div class="page-hero"><div class="eyebrow">{escape(kicker)}</div>'
        f'<h1>{escape(title)}</h1><p>{escape(description)}</p>'
        f'<div class="hero-meta">{chips_html}</div></div>',
        unsafe_allow_html=True,
    )


def section_heading(st, number, title, description=""):
    st.markdown(
        f'<div class="section-heading"><span class="section-index">{escape(number)}</span>'
        f'<div><h2>{escape(title)}</h2><p>{escape(description)}</p></div></div>',
        unsafe_allow_html=True,
    )
