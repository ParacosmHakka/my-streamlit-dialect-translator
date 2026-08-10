import re
import streamlit as st

TONES = {
    "1": "²²⁴",
    "2": "³⁴¹",
    "3": "²¹",
    "4": "⁵³",
    "5": "⁴¹",
    "6": "³⁴",
    "7": "³³",
    "8": "¹³",
}

INITIALS = [
    ("ny", "ȵ"),
    ("ng", "ŋ"),
    ("b", "p"),
    ("p", "pʰ"),
    ("m", "m"),
    ("f", "f"),
    ("v", "v"),
    ("z", "ts"),
    ("c", "tsʰ"),
    ("s", "s"),
    ("d", "t"),
    ("t", "tʰ"),
    ("n", "n"),
    ("l", "l"),
    ("j", "tɕ"),
    ("q", "tɕʰ"),
    ("x", "ɕ"),
    ("g", "k"),
    ("k", "kʰ"),
    ("h", "h"),
    ("r", "ʔ"),
]

FINALS = [
    ("uaeq", "uæʔ"),
    ("yueq", "yɛʔ"),
    ("ieoq", "iɤʔ"),
    ("uaen", "uæ̃"),
    ("ieong", "iɤŋ"),
    ("iang", "iɑŋ"),
    ("iaq", "iɑʔ"),
    ("ioq", "iɔʔ"),
    ("iong", "iɔŋ"),
    ("aen", "æ̃"),
    ("aeq", "æʔ"),
    ("eoq", "ɤʔ"),
    ("eong", "ɤŋ"),
    ("ien", "iɪ̃"),
    ("iun", "iũ"),
    ("uei", "uei"),
    ("ua", "uɑ"),
    ("ue", "uɛ"),
    ("un", "ũ"),
    ("yun", "yn"),
    ("iei", "iei"),
    ("iou", "iou"),
    ("ieu", "iəɯ"),
    ("ieq", "iɛʔ"),
    ("io", "iɔ"),
    ("ia", "iɑ"),
    ("ang", "ɑŋ"),
    ("ong", "ɔŋ"),
    ("ou", "ou"),
    ("eu", "əɯ"),
    ("ei", "ei"),
    ("en", "en"),
    ("aq", "ɑʔ"),
    ("a", "ɑ"),
    ("oq", "ɔʔ"),
    ("o", "ɔ"),
    ("eq", "ɛʔ"),
    ("e", "ɛ"),
    ("iq", "iʔ"),
    ("in", "in"),
    ("u", "u"),
    ("i", "i"),
    ("n", "n̩"),
]

I18N = {
    "zh": {
        "page_title": "会昌话拼音转音标工具",
        "title": "会昌话拼音转国际音标",
        "subtitle": "请输入会昌话罗马字拼音（支持单字、词语、整句及标点符号）：",
        "input_label": "输入拼音：",
        "btn_convert": "一键转换",
        "success": "转换成功！",
        "result_header": "转换结果（IPA）：",
        "warning_empty": "请先输入拼音！",
        "lang_select": "选择语言 / Select Language",
    },
    "en": {
        "page_title": "Huichang Romanization to IPA Converter",
        "title": "Huichang Romanization to IPA Converter",
        "subtitle": "Enter Huichang Romanization pinyin (supports words, sentences, and punctuation):",
        "input_label": "Input Pinyin:",
        "btn_convert": "Convert to IPA",
        "success": "Conversion Successful!",
        "result_header": "Conversion Result (IPA):",
        "warning_empty": "Please enter pinyin first!",
        "lang_select": "Select Language / 选择语言",
    },
}


def convert_syllable(syllable):
    """转换单个音节"""
    tone_match = re.search(r"\d$", syllable)
    if not tone_match:
        return syllable
    tone_num = tone_match.group()
    tone_ipa = TONES.get(tone_num, "")
    core = syllable[:-1]

    if core == "n":
        return f"n̩{tone_ipa}"

    parsed_initial = ""
    parsed_initial_ipa = ""
    for py, ipa in INITIALS:
        if core.startswith(py):
            parsed_initial = py
            parsed_initial_ipa = ipa
            break

    final_pinyin = core[len(parsed_initial) :]

    parsed_final_ipa = ""
    if final_pinyin == "i" and parsed_initial in ["z", "c", "s"]:
        parsed_final_ipa = "ɿ"
    else:
        for py, ipa in FINALS:
            if final_pinyin == py:
                parsed_final_ipa = ipa
                break

    return f"{parsed_initial_ipa}{parsed_final_ipa}{tone_ipa}"


def convert_text(text):
    """按句号/问号/感叹号分段，整句包裹在 / ... / 内"""
    segments = re.split(r"([.?!。？！\n]+)", text)

    result = []
    for segment in segments:
        if not segment:
            continue
        if re.match(r"^[.?!。？！\n]+$", segment):
            result.append(segment)
            continue

        tokens = re.findall(r"[a-zA-Z]+\d|[^a-zA-Z\d]+", segment)
        ipa_tokens = []
        for token in tokens:
            if re.match(r"^[a-zA-Z]+\d$", token):
                ipa_tokens.append(convert_syllable(token.lower()))
            else:
                ipa_tokens.append(token)

        seg_ipa = "".join(ipa_tokens).strip()
        if seg_ipa:
            result.append(f"/{seg_ipa}/")

    return "".join(result)

st.set_page_config(page_title="Huichang IPA Converter", layout="centered")

lang_choice = st.sidebar.selectbox(
    "Language / 语言", options=["中文", "English"], index=0
)

lang_code = "zh" if lang_choice == "中文" else "en"
t = I18N[lang_code]

st.title(t["title"])
st.write(t["subtitle"])

input_text = st.text_area(
    t["input_label"],
    value="hen1 ho3!",
    height=120,
)

if st.button(t["btn_convert"], type="primary"):
    if input_text.strip():
        output_ipa = convert_text(input_text)
        st.success(t["success"])
        st.subheader(t["result_header"])
        st.code(output_ipa, language=None)
    else:
        st.warning(t["warning_empty"])
