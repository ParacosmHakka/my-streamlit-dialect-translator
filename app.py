import re
import streamlit as st
import pandas as pd

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
    ("iun", "iũ"),
    ("uei", "uei"),
    ("ua", "uɑ"),
    ("ue", "uɛ"),
    ("un", "ũ"),
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

    final_pinyin = core[len(parsed_initial):]
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
    if not text or text == "None":
        return ""
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

st.set_page_config(page_title="会昌话发音查询网", layout="wide")

if "language" not in st.session_state:
    st.session_state["language"] = "简体中文"

if "search_modes" not in st.session_state:
    st.session_state["search_modes"] = ["字词查询", "句子查询"]

if "tool_select" not in st.session_state:
    st.session_state["tool_select"] = "方言词条检索"

try:
    excel_file = "dialect_data.xlsx"
    df_hc_words = pd.read_excel(excel_file, sheet_name="会昌话字词查询")
    df_hc_sents = pd.read_excel(excel_file, sheet_name="会昌话句子查询")
except Exception as e:
    st.error(f"读取文件失败，请检查文件和工作表名称：{e}")
    st.stop()


def get_ui_text(lang):
    if lang == "简体中文":
        return {
            "lang_sidebar": "Language / 语言",
            "tool_title": "功能选择",
            "search_func": "方言词条检索",
            "ipa_func": "拼音‑国际音标转换器",
            "title": "会昌话发音查询系统",
            "sub": "仅供个人使用 | 不定时更新",
            "select_mode": "选择查询内容",
            "words": "字词查询",
            "sents": "句子查询",
            "filter_type": "按类型筛选",
            "all": "全部",
            "search_label": "在这里输入你想查询的汉字、词语或用法（支持模糊搜索）：",
            "no_data": "没有找到匹配的数据，换个词试试吧！",
            "result_title": "查询结果",
            "mandarin": "对应普通话",
            "usage": "用法示例",
            "ipa": "国际音标",
            "pinyin_input": "输入会昌话拼音",
            "convert_btn": "一键转换音标",
            "out_ipa": "转换结果"
        }
    elif lang == "繁體中文":
        return {
            "lang_sidebar": "語言 / Language",
            "tool_title": "功能選擇",
            "search_func": "方言詞條檢索",
            "ipa_func": "拼音‑國際音標轉換器",
            "title": "會昌話發音查詢系統",
            "sub": "僅供個人使用｜不定時更新",
            "select_mode": "選擇查詢內容",
            "words": "字詞查詢",
            "sents": "句子查詢",
            "filter_type": "按類型篩選",
            "all": "全部",
            "search_label": "在此輸入你想要查詢漢字、詞語或是用法（支援模糊搜尋）：",
            "no_data": "找不到相符資料，試試其他關鍵字！",
            "result_title": "查詢結果",
            "mandarin": "對應普通話",
            "usage": "用法示例",
            "ipa": "國際音標",
            "pinyin_input": "輸入會昌話拼音",
            "convert_btn": "一鍵轉換音標",
            "out_ipa": "轉換結果"
        }
    elif lang == "English":
        return {
            "lang_sidebar": "Language",
            "tool_title": "Function",
            "search_func": "Dialect Search",
            "ipa_func": "Pinyin‑IPA Converter",
            "title": "Huichang Dialect Query System",
            "sub": "Personal Use Only | Update via Excel Anytime",
            "select_mode": "Select Mode",
            "words": "Word Search",
            "sents": "Sentence Search",
            "filter_type": "Filter Type",
            "all": "All",
            "search_label": "Search Here (Type Chinese character or meaning):",
            "no_data": "No data found.",
            "result_title": "Result",
            "mandarin": "Mandarin",
            "usage": "Usage",
            "ipa": "IPA",
            "pinyin_input": "Input Huichang Pinyin",
            "convert_btn": "Convert",
            "out_ipa": "IPA Output"
        }


st.session_state["language"] = st.sidebar.radio(
    label=get_ui_text(st.session_state["language"])["lang_sidebar"],
    options=["简体中文", "繁體中文", "English"],
    key="lang_select"
)
ui = get_ui_text(st.session_state["language"])

st.sidebar.header(ui["tool_title"])
st.session_state["tool_select"] = st.sidebar.radio("", [ui["search_func"], ui["ipa_func"]], key="tool_radio")

if st.session_state["tool_select"] == ui["search_func"]:
    st.sidebar.markdown(f"**{ui['select_mode']}**")
    mode_options = [ui["words"], ui["sents"]]
    selected_modes = []
    for mode in mode_options:
        checked = st.sidebar.checkbox(mode, value=(mode in st.session_state.get("search_modes", mode_options)),
                                        key=f"mode_{mode}")
        if checked:
            selected_modes.append(mode)
    st.session_state["search_modes"] = selected_modes
    if not selected_modes:
        st.sidebar.warning("请至少选择一种查询模式")
        selected_modes = mode_options

    is_words_mode = ui["words"] in selected_modes
    is_sents_mode = ui["sents"] in selected_modes
    combined_dfs = []
    if is_words_mode:
        combined_dfs.append(df_hc_words)
    if is_sents_mode:
        combined_dfs.append(df_hc_sents)

    current_df = pd.concat(combined_dfs, ignore_index=True)
    char_col = "会昌话正字"
    pinyin_col = "会昌话拼音"

    if "类型" in current_df.columns:
        all_types = [ui["all"]] + sorted(list(current_df["类型"].dropna().unique()))
        type_choice = st.sidebar.selectbox(ui["filter_type"], all_types, key="type_filter")
    else:
        type_choice = ui["all"]

    st.title(ui["title"])
    st.caption(ui["sub"])
    search_query = st.text_input(ui["search_label"], "").strip()
    filtered_df = current_df.copy()
    if type_choice != ui["all"] and "类型" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["类型"] == type_choice]

    if search_query:
        mask = pd.Series(False, index=filtered_df.index)
        match_info = {}
        for idx in filtered_df.index:
            score = 0
            if "普通话" in filtered_df.columns:
                val = str(filtered_df.loc[idx, "普通话"]) if pd.notna(filtered_df.loc[idx, "普通话"]) else ""
                if search_query in val:
                    mask.loc[idx] = True
                    if val == search_query:
                        score += 10
                    elif val.startswith(search_query):
                        score += 5
                    else:
                        score += 2
                    score += max(0, 10 - len(val))

            if char_col in filtered_df.columns:
                val = str(filtered_df.loc[idx, char_col]) if pd.notna(filtered_df.loc[idx, char_col]) else ""
                if search_query in val:
                    mask.loc[idx] = True
                    if val == search_query:
                        score += 10
                    elif val.startswith(search_query):
                        score += 5
                    else:
                        score += 2
                    score += max(0, 10 - len(val))

            if "用法" in filtered_df.columns:
                val = str(filtered_df.loc[idx, "用法"]) if pd.notna(filtered_df.loc[idx, "用法"]) else ""
                if search_query in val:
                    mask.loc[idx] = True
                    score += 1
            match_info[idx] = score

        filtered_df = filtered_df[mask]
        if not filtered_df.empty:
            filtered_df['_match_score'] = filtered_df.index.map(lambda x: match_info.get(x, 0))
            filtered_df = filtered_df.sort_values('_match_score', ascending=False)
            filtered_df = filtered_df.drop('_match_score', axis=1)

    st.subheader(ui["result_title"])
    if filtered_df.empty:
        st.info(ui["no_data"])
    else:
        for _, row in filtered_df.iterrows():
            row = row.fillna("")
            word_to_show = row[char_col] if (char_col in row and row[char_col]) else row.get('普通话', '')
            display_title = f"{word_to_show}"
            if "读法类型" in row and row['读法类型']:
                display_title += f" ({row['读法类型']})"
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"### **{display_title}**")
                    pinyin_val = row.get(pinyin_col, '')
                    ipa_val = convert_text(pinyin_val)
                    st.markdown(f"**会昌话拼音:** `{pinyin_val}`")
                    st.markdown(f"**{ui['ipa']}:** `{ipa_val}`")
                with col2:
                    st.markdown(f"**{ui['mandarin']}:** {row.get('普通话', '')}")
                    if "用法" in row and row["用法"]:
                        st.markdown(f"💡 **{ui['usage']}:** {row['用法']}")
                st.divider()

elif st.session_state["tool_select"] == ui["ipa_func"]:
    st.title(ui["ipa_func"])
    input_py = st.text_area(ui["pinyin_input"], value="hen1 ho3，nge1 jio2 xio3 kiong2", height=140)
    if st.button(ui["convert_btn"], type="primary"):
        if input_py.strip():
            res = convert_text(input_py)
            st.success(ui["out_ipa"])
            st.code(res)
        else:
            st.warning("请输入方言拼音")
