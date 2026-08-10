import re
import streamlit as st

# 1. 声调映射
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

# 2. 声母映射
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

# 3. 韵母映射
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


def convert_syllable(syllable):
    """转换单个音节"""
    tone_match = re.search(r"\d$", syllable)
    if not tone_match:
        return syllable
    tone_num = tone_match.group()
    tone_ipa = TONES.get(tone_num, "")
    core = syllable[:-1]

    # 特殊情况处理：成音节辅音 n（如 n1, n2, n3）
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
    # 根据句末标点（. ? ! 。 ？ ！）及换行符切分成分句
    segments = re.split(r"([.?!。？！\n]+)", text)

    result = []
    for segment in segments:
        if not segment:
            continue
        # 如果是句末标点或换行符，直接保留在外侧
        if re.match(r"^[.?!。？！\n]+$", segment):
            result.append(segment)
            continue

        # 匹配拼音音节与非拼音符号（如逗号、空格）
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


# ================= Streamlit 界面构建 =================
st.set_page_config(page_title="会昌话拼音转换工具", layout="centered")

st.title("会昌话拼音一键转国际音标")
st.write("请输入会昌话罗马字拼音（支持单字、词语、整句及标点符号）：")

# 文本输入框
input_text = st.text_area(
    "输入拼音：",
    value="hen1 ho3，nge1 jio2 xio3 kiong2，hen1 jio2 n1 ge3？",
    height=120,
)

# 转换按钮
if st.button("一键转换", type="primary"):
    if input_text.strip():
        output_ipa = convert_text(input_text)
        st.success("转换成功！")
        st.subheader("转换结果（IPA）：")
        st.code(output_ipa, language=None)
    else:
        st.warning("请先输入拼音！")
