import re
import pandas as pd
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
    ("iun", "iũ"),
    ("uei", "uei"),
    ("uen", "uen"),
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
    ("y", "ɿ"),
    ("i", "i"),
    ("n", "n̩"),
]

INITIAL_PATTERNS = sorted([py for py, _ in INITIALS], key=len, reverse=True)
FINAL_PATTERNS = sorted([py for py, _ in FINALS], key=len, reverse=True)
TONE_ORDER = ["1", "2", "3", "4", "5", "6", "7", "8"]
INITIAL_ORDER = [py for py, _ in INITIALS]
FINAL_ORDER = [py for py, _ in FINALS]


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
    final_pinyin = core[len(parsed_initial) :]
    parsed_final_ipa = ""
    for py, ipa in FINALS:
        if final_pinyin == py:
            parsed_final_ipa = ipa
            break
    return f"{parsed_initial_ipa}{parsed_final_ipa}{tone_ipa}"


def convert_text(text):
    if pd.isna(text):
        text = ""
    text = str(text)
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


def parse_pinyin_query(query):
    if not query:
        return "", "", False
    query_lower = query.lower().strip()
    has_tone = bool(re.search(r"\d$", query_lower))
    core = query_lower[:-1] if has_tone else query_lower
    matched_initial = ""
    for py in INITIAL_PATTERNS:
        if core.startswith(py):
            matched_initial = py
            break
    final_part = core[len(matched_initial) :]
    return matched_initial, final_part, has_tone


def get_pinyin_components(syllable):
    tone_match = re.search(r"(\d)$", syllable)
    core = syllable[:-1] if tone_match else syllable
    tone = tone_match.group(1) if tone_match else ""
    matched_initial = ""
    for py in INITIAL_PATTERNS:
        if core.startswith(py):
            matched_initial = py
            break
    final_part = core[len(matched_initial) :]
    return matched_initial, final_part, tone


def get_entry_type_priority(row):
    t = str(row.get("类型", ""))
    if t == "单字":
        return 0
    elif t == "词语":
        return 1
    else:
        return 2


def sort_by_pinyin(df, query, selected_tones):
    if df.empty:
        return df
    pinyin_col = "会昌话拼音"
    if pinyin_col not in df.columns:
        return df
    char_col = "会昌话正字"
    query_lower = query.lower().strip()
    df["_type_priority"] = df.apply(get_entry_type_priority, axis=1)
    df["_char_len"] = df[char_col].astype(str).apply(len)

    def get_sort_key(row):
        pinyin_val = str(row.get(pinyin_col, ""))
        if pd.isna(pinyin_val) or pinyin_val == "":
            return (9999, 9999, 9999, 9999, 9999, 9999)
        syllables = pinyin_val.split()
        if not syllables:
            return (9999, 9999, 9999, 9999, 9999, 9999)
        best_match_score = 9999
        best_len = 9999
        best_initial_idx = 9999
        best_final_idx = 9999
        best_tone_idx = 9999
        entry_type = row.get("类型", "")
        for syl in syllables:
            tone_match = re.search(r"(\d)$", syl)
            core = syl[:-1] if tone_match else syl
            tone = tone_match.group(1) if tone_match else ""
            matched_initial = ""
            for py in INITIAL_PATTERNS:
                if core.startswith(py):
                    matched_initial = py
                    break
            final_part = core[len(matched_initial) :]
            match_score = 9999
            if query_lower == syl:
                match_score = 0
            elif query_lower == core:
                match_score = 1
            elif core.startswith(query_lower):
                match_score = 2
            elif query_lower in core:
                match_score = 3 + core.find(query_lower)
            else:
                match_score = 9999
            syl_len = len(core)
            initial_idx = (
                INITIAL_ORDER.index(matched_initial)
                if matched_initial in INITIAL_ORDER
                else 9999
            )
            final_idx = (
                FINAL_ORDER.index(final_part)
                if final_part in FINAL_ORDER
                else 9999
            )
            tone_idx = TONE_ORDER.index(tone) if tone in TONE_ORDER else 9999
            if match_score < best_match_score:
                best_match_score = match_score
                best_len = syl_len
                best_initial_idx = initial_idx
                best_final_idx = final_idx
                best_tone_idx = tone_idx
            elif match_score == best_match_score and syl_len < best_len:
                best_len = syl_len
                best_initial_idx = initial_idx
                best_final_idx = final_idx
                best_tone_idx = tone_idx
        char_len = row.get("_char_len", 0)
        if entry_type == "单字":
            return (
                best_match_score,
                best_len,
                best_initial_idx,
                best_final_idx,
                best_tone_idx,
                char_len,
            )
        else:
            return (best_match_score, best_len, char_len, 9999, 9999, 9999)

    df["_sort_key"] = df.apply(get_sort_key, axis=1)
    df = df.sort_values(
        ["_type_priority", "_sort_key"], ascending=[True, True]
    )
    df = df.drop(["_sort_key", "_type_priority", "_char_len"], axis=1)
    return df


def filter_by_pinyin(df, query, selected_tones):
    if df.empty:
        return df
    pinyin_col = "会昌话拼音"
    if pinyin_col not in df.columns:
        return df
    initial, final, has_tone = parse_pinyin_query(query)
    if not query:
        if selected_tones:

            def has_selected_tone(pinyin_val):
                if pd.isna(pinyin_val) or pinyin_val == "":
                    return False
                syllables = str(pinyin_val).split()
                for syl in syllables:
                    tone_match = re.search(r"(\d)$", syl)
                    if tone_match and tone_match.group(1) in selected_tones:
                        return True
                return False

            mask = df[pinyin_col].astype(str).apply(has_selected_tone)
            result_df = df[mask].copy()
            if not result_df.empty:
                result_df = sort_by_pinyin(result_df, query, selected_tones)
            return result_df
        return df

    def match_pinyin(pinyin_val):
        if pd.isna(pinyin_val) or pinyin_val == "":
            return False
        pinyin_str = str(pinyin_val).lower().strip()
        syllables = pinyin_str.split()
        for syl in syllables:
            tone_match = re.search(r"(\d)$", syl)
            tone = tone_match.group(1) if tone_match else ""
            if selected_tones and tone not in selected_tones:
                continue
            core = syl[:-1] if tone_match else syl
            matched_initial = ""
            for py in INITIAL_PATTERNS:
                if core.startswith(py):
                    matched_initial = py
                    break
            final_part = core[len(matched_initial) :]
            initial_match = core.startswith(initial) if initial else True
            final_match = (final_part == final) if final else True
            if initial_match and final_match:
                return True
        return False

    mask = df[pinyin_col].astype(str).apply(match_pinyin)
    result_df = df[mask].copy()
    if not result_df.empty:
        result_df = sort_by_pinyin(result_df, query, selected_tones)
    return result_df


def filter_readings_common(df, show_old, show_new):
    if show_old and show_new:
        return df
    mask = pd.Series(True, index=df.index)
    for idx, row in df.iterrows():
        rt = str(row.get("读法类型", ""))
        has_old = "老派" in rt
        has_new = "新派" in rt
        if has_old and has_new:
            keep = show_old or show_new
        elif has_old:
            keep = show_old
        elif has_new:
            keep = show_new
        else:
            keep = True
        mask.loc[idx] = keep
    return df[mask]


def is_variant_type(rt):
    rt_str = str(rt) if pd.notna(rt) else ""
    return any(k in rt_str for k in ["新派", "老派", "文读", "白读"])


def group_by_character(df):
    if df.empty:
        return df
    char_col = "会昌话正字"
    if char_col not in df.columns:
        return df
    grouped = []
    for char, group in df.groupby(char_col, sort=False):
        if len(group) > 1:
            all_variant = all(
                is_variant_type(r.get("读法类型", ""))
                for _, r in group.iterrows()
            )
            usages = group["用法"].fillna("").astype(str).unique()
            usages = [u for u in usages if u.strip()]
            same_usage = len(usages) <= 1
            if all_variant or same_usage:
                readings = []
                for _, row in group.iterrows():
                    pinyin = str(row.get("会昌话拼音", ""))
                    ipa = convert_text(pinyin)
                    rt = str(row.get("读法类型", ""))
                    readings.append({"pinyin": pinyin, "ipa": ipa, "type": rt})
                merged_row = group.iloc[0].to_dict()
                merged_row["_readings"] = readings
                merged_row["_is_grouped"] = True
                merged_row["_type_priority"] = get_entry_type_priority(
                    group.iloc[0]
                )
                merged_row["_char_len"] = len(str(char))
                grouped.append(merged_row)
            else:
                for _, row in group.iterrows():
                    row_dict = row.to_dict()
                    pinyin = str(row_dict.get("会昌话拼音", ""))
                    row_dict["_ipa"] = convert_text(pinyin)
                    row_dict["_is_grouped"] = False
                    row_dict["_type_priority"] = get_entry_type_priority(row)
                    row_dict["_char_len"] = len(str(char))
                    grouped.append(row_dict)
        else:
            row_dict = group.iloc[0].to_dict()
            pinyin = str(row_dict.get("会昌话拼音", ""))
            row_dict["_ipa"] = convert_text(pinyin)
            row_dict["_is_grouped"] = False
            row_dict["_type_priority"] = get_entry_type_priority(group.iloc[0])
            row_dict["_char_len"] = len(str(char))
            grouped.append(row_dict)
    result_df = pd.DataFrame(grouped)
    if "_sort_key" in result_df.columns:
        result_df = result_df.drop("_sort_key", axis=1)
    return result_df


@st.cache_resource
def load_excel_data():
    excel_file = "dialect_data.xlsx"
    df_hc_chars = pd.read_excel(excel_file, sheet_name="会昌话单字查询").fillna("")
    df_hc_words = pd.read_excel(excel_file, sheet_name="会昌话词语查询").fillna("")
    df_hc_sents = pd.read_excel(excel_file, sheet_name="会昌话句子查询").fillna("")
    df_hc_chars["类型"] = "单字"
    df_hc_words["类型"] = "词语"
    df_hc_sents["类型"] = "句子"
    return df_hc_chars, df_hc_words, df_hc_sents


st.set_page_config(page_title="会昌话发音查询网", layout="wide")

if "language" not in st.session_state:
    st.session_state["language"] = "简体中文"
if "search_modes" not in st.session_state:
    st.session_state["search_modes"] = ["单字查询", "词语查询", "句子查询"]
if "tool_select" not in st.session_state:
    st.session_state["tool_select"] = "方言词条检索"
if "search_type" not in st.session_state:
    st.session_state["search_type"] = "汉字查询"
if "selected_tones" not in st.session_state:
    st.session_state["selected_tones"] = []
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "ipa_input" not in st.session_state:
    st.session_state["ipa_input"] = "hen1 ho3，hen1 jio2 n7 gei3?"
if "show_old_reading" not in st.session_state:
    st.session_state["show_old_reading"] = True
if "show_new_reading" not in st.session_state:
    st.session_state["show_new_reading"] = True

try:
    df_hc_chars, df_hc_words, df_hc_sents = load_excel_data()
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
            "words": "单字查询",
            "phrases": "词语查询",
            "sents": "句子查询",
            "search_label": "在这里输入你想查询的汉字或词语（支持模糊搜索）：",
            "pinyin_search_label": "在这里输入会昌话拼音（支持声母/韵母/完整音节）：",
            "no_data": "没有找到匹配的数据，换个词试试吧！",
            "result_title": "查询结果",
            "entry_count": "条目数量：{}",
            "mandarin": "对应普通话",
            "usage": "用法示例",
            "ipa": "国际音标",
            "pinyin_input": "输入会昌话拼音",
            "convert_btn": "一键转换音标",
            "out_ipa": "转换结果",
            "char_count": "当前收录单字：{} 个",
            "phrase_count": "当前收录词语：{} 个",
            "sent_count": "当前收录句子：{} 个",
            "search_type_label": "查询方式",
            "hanzi_search": "汉字查询",
            "pinyin_search": "拼音查询",
            "tone_filter_label": "声调过滤",
            "tone_all": "全部声调",
            "warning_select_mode": "请至少选择一种查询模式",
            "pinyin_col": "会昌话拼音",
            "ipa_col": "国际音标",
            "new_school": "新派",
            "old_school": "老派",
            "reading_type": "读法类型",
            "reading_filter_label": "读音派别过滤",
            "show_old": "显示老派读音",
            "show_new": "显示新派读音",
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
            "words": "單字查詢",
            "phrases": "詞語查詢",
            "sents": "句子查詢",
            "search_label": "在此輸入你想要查詢漢字或詞語（支持模糊搜尋）：",
            "pinyin_search_label": "在此輸入會昌話拼音（支持聲母/韻母/完整音節）：",
            "no_data": "找不到相符資料，試試其他關鍵字！",
            "result_title": "查詢結果",
            "entry_count": "條目數量：{}",
            "mandarin": "對應普通話",
            "usage": "用法示例",
            "ipa": "國際音標",
            "pinyin_input": "輸入會昌話拼音",
            "convert_btn": "一鍵轉換音標",
            "out_ipa": "轉換結果",
            "char_count": "當前收錄單字：{} 個",
            "phrase_count": "當前收錄詞語：{} 個",
            "sent_count": "當前收錄句子：{} 個",
            "search_type_label": "查詢方式",
            "hanzi_search": "漢字查詢",
            "pinyin_search": "拼音查詢",
            "tone_filter_label": "聲調過濾",
            "tone_all": "全部聲調",
            "warning_select_mode": "請至少選擇一種查詢模式",
            "pinyin_col": "會昌話拼音",
            "ipa_col": "國際音標",
            "new_school": "新派",
            "old_school": "老派",
            "reading_type": "讀法類型",
            "reading_filter_label": "讀音派別過濾",
            "show_old": "顯示老派讀音",
            "show_new": "顯示新派讀音",
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
            "words": "Character Search",
            "phrases": "Phrase Search",
            "sents": "Sentence Search",
            "search_label": "Search Here (Type Chinese character or meaning):",
            "pinyin_search_label": (
                "Enter Huichang Pinyin (supports initial/final/syllable):"
            ),
            "no_data": "No data found.",
            "result_title": "Result",
            "entry_count": "Entries: {}",
            "mandarin": "Mandarin",
            "usage": "Usage",
            "ipa": "IPA",
            "pinyin_input": "Input Huichang Dialect Pinyin",
            "convert_btn": "Convert",
            "out_ipa": "Conversion Successful!",
            "char_count": "Characters: {}",
            "phrase_count": "Phrases: {}",
            "sent_count": "Sentences: {}",
            "search_type_label": "Search Type",
            "hanzi_search": "Character Search",
            "pinyin_search": "Pinyin Search",
            "tone_filter_label": "Tone Filter",
            "tone_all": "All Tones",
            "warning_select_mode": "Please select at least one search mode",
            "pinyin_col": "Huichang Pinyin",
            "ipa_col": "IPA",
            "new_school": "New School",
            "old_school": "Old School",
            "reading_type": "Reading Type",
            "reading_filter_label": "Reading Type Filter",
            "show_old": "Show Old School",
            "show_new": "Show New School",
        }


lang = st.sidebar.radio(
    label=get_ui_text(st.session_state["language"])["lang_sidebar"],
    options=["简体中文", "繁體中文", "English"],
    key="lang_select",
)
st.session_state["language"] = lang
ui = get_ui_text(st.session_state["language"])

st.sidebar.header(ui["tool_title"])
tool_options = [ui["search_func"], ui["ipa_func"]]
current_tool = st.session_state.get("tool_select", ui["search_func"])
if current_tool not in tool_options:
    current_tool = ui["search_func"]
    st.session_state["tool_select"] = current_tool
selected_tool = st.sidebar.radio(
    "", tool_options, index=tool_options.index(current_tool), key="tool_radio"
)
st.session_state["tool_select"] = selected_tool

if st.session_state["tool_select"] == ui["search_func"]:
    st.sidebar.markdown(f"**{ui['select_mode']}**")
    mode_options = [ui["words"], ui["phrases"], ui["sents"]]
    current_modes = st.session_state.get("search_modes", mode_options.copy())
    current_modes = [m for m in current_modes if m in mode_options]
    if not current_modes:
        current_modes = mode_options.copy()
    selected_modes = []
    for mode in mode_options:
        checked = st.sidebar.checkbox(
            mode, value=(mode in current_modes), key=f"mode_{mode}"
        )
        if checked:
            selected_modes.append(mode)
    st.session_state["search_modes"] = selected_modes
    if not selected_modes:
        st.sidebar.warning(ui["warning_select_mode"])
        selected_modes = mode_options

    current_search_type = st.session_state.get(
        "search_type", ui["hanzi_search"]
    )
    selected_tones = []
    if current_search_type == ui["pinyin_search"]:
        st.sidebar.markdown(f"**{ui['tone_filter_label']}**")
        tone_options = ["1", "2", "3", "4", "5", "6", "7", "8"]
        tone_display = {
            "1": f"1 {TONES['1']}",
            "2": f"2 {TONES['2']}",
            "3": f"3 {TONES['3']}",
            "4": f"4 {TONES['4']}",
            "5": f"5 {TONES['5']}",
            "6": f"6 {TONES['6']}",
            "7": f"7 {TONES['7']}",
            "8": f"8 {TONES['8']}",
        }
        for t in tone_options:
            checked = st.sidebar.checkbox(
                tone_display[t],
                value=(t in st.session_state.get("selected_tones", [])),
                key=f"tone_{t}",
            )
            if checked:
                selected_tones.append(t)
    st.session_state["selected_tones"] = selected_tones

    st.sidebar.markdown(f"**{ui['reading_filter_label']}**")
    show_old = st.sidebar.checkbox(
        ui["show_old"],
        value=st.session_state.get("show_old_reading", True),
        key="show_old_reading",
    )
    show_new = st.sidebar.checkbox(
        ui["show_new"],
        value=st.session_state.get("show_new_reading", True),
        key="show_new_reading",
    )

    is_words_mode = ui["words"] in selected_modes
    is_phrases_mode = ui["phrases"] in selected_modes
    is_sents_mode = ui["sents"] in selected_modes
    combined_dfs = []
    if is_words_mode:
        df_chars_filtered = filter_readings_common(
            df_hc_chars.copy(), show_old, show_new
        )
        combined_dfs.append(df_chars_filtered)
    if is_phrases_mode:
        df_words_filtered = filter_readings_common(
            df_hc_words.copy(), show_old, show_new
        )
        combined_dfs.append(df_words_filtered)
    if is_sents_mode:
        df_sents_filtered = filter_readings_common(
            df_hc_sents.copy(), show_old, show_new
        )
        combined_dfs.append(df_sents_filtered)
    current_df = pd.concat(combined_dfs, ignore_index=True)
    char_col = "会昌话正字"
    pinyin_col = "会昌话拼音"
    st.title(ui["title"])
    st.caption(ui["sub"])
    col_search_input, col_search_type = st.columns([5, 1])
    with col_search_input:
        if (
            st.session_state.get("search_type", ui["hanzi_search"])
            == ui["hanzi_search"]
        ):
            search_query = st.text_input(
                ui["search_label"],
                value=st.session_state.get("search_query", ""),
                key="search_input",
            )
        else:
            search_query = st.text_input(
                ui["pinyin_search_label"],
                value=st.session_state.get("search_query", ""),
                key="search_input",
            )
        st.session_state["search_query"] = search_query
    with col_search_type:
        st.write("")
        current_search_type = st.session_state.get(
            "search_type", ui["hanzi_search"]
        )
        if current_search_type not in [ui["hanzi_search"], ui["pinyin_search"]]:
            current_search_type = ui["hanzi_search"]
        search_type = st.radio(
            ui["search_type_label"],
            [ui["hanzi_search"], ui["pinyin_search"]],
            index=0 if current_search_type == ui["hanzi_search"] else 1,
            key="search_type_radio",
            label_visibility="collapsed",
            horizontal=False,
        )
        st.session_state["search_type"] = search_type
    unique_chars = len(df_hc_chars[char_col].unique()) if is_words_mode else 0
    unique_words = len(df_hc_words[char_col].unique()) if is_phrases_mode else 0
    if len(selected_modes) == 1:
        if ui["words"] in selected_modes:
            st.caption(ui["char_count"].format(unique_chars))
        elif ui["phrases"] in selected_modes:
            st.caption(ui["phrase_count"].format(unique_words))
        elif ui["sents"] in selected_modes:
            st.caption(ui["sent_count"].format(len(df_hc_sents)))
    else:
        count_parts = []
        if ui["words"] in selected_modes:
            count_parts.append(ui["char_count"].format(unique_chars))
        if ui["phrases"] in selected_modes:
            count_parts.append(ui["phrase_count"].format(unique_words))
        if ui["sents"] in selected_modes:
            count_parts.append(ui["sent_count"].format(len(df_hc_sents)))
        st.caption(" | ".join(count_parts))
    filtered_df = current_df.copy()
    if search_type == ui["hanzi_search"]:
        if search_query:
            mask = pd.Series(False, index=filtered_df.index)
            for idx in filtered_df.index:
                val_char = (
                    str(filtered_df.loc[idx, char_col])
                    if pd.notna(filtered_df.loc[idx, char_col])
                    else ""
                )
                if search_query in val_char:
                    mask.loc[idx] = True
                if "普通话" in filtered_df.columns and not mask.loc[idx]:
                    val_mand = (
                        str(filtered_df.loc[idx, "普通话"])
                        if pd.notna(filtered_df.loc[idx, "普通话"])
                        else ""
                    )
                    if search_query in val_mand:
                        mask.loc[idx] = True
            filtered_df = filtered_df[mask]
            if not filtered_df.empty:
                filtered_df["_type_priority"] = filtered_df.apply(
                    get_entry_type_priority, axis=1
                )
                filtered_df["_char_len"] = filtered_df[char_col].astype(
                    str
                ).apply(len)
                filtered_df = filtered_df.sort_values(
                    ["_type_priority", "_char_len"], ascending=[True, True]
                )
                filtered_df = filtered_df.drop(
                    ["_type_priority", "_char_len"], axis=1
                )
    else:
        filtered_df = filter_by_pinyin(
            filtered_df, search_query, st.session_state.get("selected_tones", [])
        )
    grouped_df = group_by_character(filtered_df)
    st.subheader(ui["result_title"])
    if grouped_df.empty:
        st.caption(ui["entry_count"].format(0))
        st.info(ui["no_data"])
    else:
        st.caption(ui["entry_count"].format(len(grouped_df)))
        for _, row in grouped_df.iterrows():
            row = row.fillna("")
            word_to_show = row.get(char_col, "")
            if not word_to_show:
                word_to_show = row.get("普通话", "")
            display_title = f"{word_to_show}"
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"### **{display_title}**")
                    if row.get("_is_grouped", False):
                        readings = row.get("_readings", [])
                        for idx, r in enumerate(readings):
                            rt = str(r.get("type", ""))
                            if "新派" in rt:
                                disp_t = ui["new_school"]
                            elif "老派" in rt:
                                disp_t = ui["old_school"]
                            else:
                                disp_t = rt if rt else ""
                            if disp_t:
                                st.markdown(f"**{disp_t}**")
                            st.markdown(
                                f"**{ui['pinyin_col']}:** `{r['pinyin']}`"
                            )
                            st.markdown(f"**{ui['ipa_col']}:** `{r['ipa']}`")
                            if idx < len(readings) - 1:
                                st.markdown("---")
                    else:
                        pinyin_val = row.get(pinyin_col, "")
                        ipa_val = row.get("_ipa", convert_text(pinyin_val))
                        rt = str(row.get("读法类型", ""))
                        if "新派" in rt:
                            disp_t = ui["new_school"]
                        elif "老派" in rt:
                            disp_t = ui["old_school"]
                        else:
                            disp_t = rt if rt else ""
                        if disp_t:
                            st.markdown(f"**{disp_t}**")
                        st.markdown(f"**{ui['pinyin_col']}:** `{pinyin_val}`")
                        st.markdown(f"**{ui['ipa_col']}:** `{ipa_val}`")
                with col2:
                    mandarin_val = str(row.get("普通话", "")).strip()
                    if mandarin_val:
                        st.markdown(f"**{ui['mandarin']}:** {mandarin_val}")
                    if "用法" in row and row["用法"]:
                        st.markdown(f"**{ui['usage']}:** {row['用法']}")
                st.divider()
elif st.session_state["tool_select"] == ui["ipa_func"]:
    st.title(ui["ipa_func"])
    ipa_input = st.text_area(
        ui["pinyin_input"],
        value=st.session_state.get("ipa_input", "hen1 ho3，hen1 jio2 n7 gei3?"),
        height=140,
        key="ipa_textarea",
    )
    st.session_state["ipa_input"] = ipa_input
    if st.button(ui["convert_btn"], type="primary"):
        if ipa_input.strip():
            res = convert_text(ipa_input)
            st.success(ui["out_ipa"])
            st.code(res)
        else:
            st.warning("请输入方言拼音")
