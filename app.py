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
    
    final_part = core[len(matched_initial):]
    return matched_initial, final_part, has_tone


def get_pinyin_score(syllable, query_initial, query_final):
    score = 0
    tone_match = re.search(r"(\d)$", syllable)
    core = syllable[:-1] if tone_match else syllable
    
    if query_initial:
        pos = core.find(query_initial)
        if pos == 0:
            score += 0
        elif pos > 0:
            score += 100 + pos
        else:
            score += 1000
    
    if query_final:
        pos = core.find(query_final)
        if pos == 0:
            score += 0
        elif pos > 0:
            score += 100 + pos
        else:
            score += 1000
    
    score += len(core) * 10
    
    if tone_match:
        tone_num = tone_match.group(1)
        score += TONE_ORDER.index(tone_num) * 0.01
    else:
        score += 100
    
    matched_initial = ""
    for py in INITIAL_PATTERNS:
        if core.startswith(py):
            matched_initial = py
            break
    if matched_initial and matched_initial in INITIAL_ORDER:
        score += INITIAL_ORDER.index(matched_initial) * 0.0001
    
    final_part = core[len(matched_initial):]
    if final_part and final_part in FINAL_ORDER:
        score += FINAL_ORDER.index(final_part) * 0.00001
    
    if tone_match:
        tone_num = tone_match.group(1)
        score += TONE_ORDER.index(tone_num) * 0.000001
    
    return score


def get_entry_type_priority(row):
    if "类型" in row:
        if row["类型"] == "单字":
            return 0
        elif row["类型"] == "词语":
            return 1
    return 2


def filter_by_pinyin(df, query, selected_tones):
    if df.empty:
        return df
    
    pinyin_col = "会昌话拼音"
    if pinyin_col not in df.columns:
        return df
    
    initial, final, has_tone = parse_pinyin_query(query)
    
    if not query:
        if selected_tones:
            tone_pattern = r"(\d)$"
            def has_selected_tone(pinyin_val):
                if pd.isna(pinyin_val) or pinyin_val == "":
                    return False
                syllables = str(pinyin_val).split()
                for syl in syllables:
                    tone_match = re.search(tone_pattern, syl)
                    if tone_match and tone_match.group(1) in selected_tones:
                        return True
                return False
            
            mask = df[pinyin_col].astype(str).apply(has_selected_tone)
            result_df = df[mask].copy()
            if not result_df.empty:
                result_df['_type_priority'] = result_df.apply(get_entry_type_priority, axis=1)
                result_df['_sort_score'] = result_df[pinyin_col].astype(str).apply(
                    lambda x: min(get_pinyin_score(syl, initial, final) for syl in str(x).split())
                )
                result_df = result_df.sort_values(['_type_priority', '_sort_score'], ascending=[True, True])
                result_df = result_df.drop(['_type_priority', '_sort_score'], axis=1)
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
            
            initial_match = False
            final_match = False
            
            if initial:
                initial_match = core.startswith(initial)
            else:
                initial_match = True
            
            if final:
                final_match = final in core
            else:
                final_match = True
            
            if initial_match and final_match:
                return True
        
        return False
    
    mask = df[pinyin_col].astype(str).apply(match_pinyin)
    result_df = df[mask].copy()
    
    if not result_df.empty:
        result_df['_type_priority'] = result_df.apply(get_entry_type_priority, axis=1)
        result_df['_sort_score'] = result_df[pinyin_col].astype(str).apply(
            lambda x: min(get_pinyin_score(syl, initial, final) for syl in str(x).split())
        )
        result_df = result_df.sort_values(['_type_priority', '_sort_score'], ascending=[True, True])
        result_df = result_df.drop(['_type_priority', '_sort_score'], axis=1)
    
    return result_df


st.set_page_config(page_title="会昌话发音查询网", layout="wide")

if "language" not in st.session_state:
    st.session_state["language"] = "简体中文"

if "search_modes" not in st.session_state:
    st.session_state["search_modes"] = ["单字查询", "词语查询", "句子查询"]

if "tool_select" not in st.session_state:
    st.session_state["tool_select"] = "方言词条检索"

if "search_type" not in st.session_state:
    st.session_state["search_type"] = "汉字查询"

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
            "tone_filter_label": "声调过滤（可多选）",
            "tone_all": "全部声调"
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
            "tone_filter_label": "聲調過濾（可多選）",
            "tone_all": "全部聲調"
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
            "pinyin_search_label": "Enter Huichang Pinyin (supports initial/final/syllable):",
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
            "tone_filter_label": "Tone Filter (multi-select)",
            "tone_all": "All Tones"
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
    mode_options = [ui["words"], ui["phrases"], ui["sents"]]
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
    is_phrases_mode = ui["phrases"] in selected_modes
    is_sents_mode = ui["sents"] in selected_modes

    combined_dfs = []
    if is_words_mode:
        df_words_filtered = df_hc_words[df_hc_words["类型"] == "单字"]
        combined_dfs.append(df_words_filtered)
    if is_phrases_mode:
        df_phrases_filtered = df_hc_words[df_hc_words["类型"] == "词语"]
        combined_dfs.append(df_phrases_filtered)
    if is_sents_mode:
        combined_dfs.append(df_hc_sents)

    current_df = pd.concat(combined_dfs, ignore_index=True)
    char_col = "会昌话正字"
    pinyin_col = "会昌话拼音"

    st.title(ui["title"])
    st.caption(ui["sub"])
    
    col_search_input, col_search_type = st.columns([5, 1])
    
    with col_search_input:
        if st.session_state.get("search_type", "汉字查询") == ui["hanzi_search"]:
            search_query = st.text_input(ui["search_label"], "", label_visibility="visible", key="search_input")
        else:
            search_query = st.text_input(ui["pinyin_search_label"], "", label_visibility="visible", key="search_input")
    
    with col_search_type:
        st.write("")
        search_type = st.radio(
            ui["search_type_label"],
            [ui["hanzi_search"], ui["pinyin_search"]],
            key="search_type_radio",
            label_visibility="collapsed",
            horizontal=False
        )
        st.session_state["search_type"] = search_type
    
    if search_type == ui["pinyin_search"]:
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
            "8": f"8 {TONES['8']}"
        }
        selected_tones = []
        for t in tone_options:
            checked = st.sidebar.checkbox(
                tone_display[t],
                value=(t in st.session_state.get("selected_tones", [])),
                key=f"tone_{t}"
            )
            if checked:
                selected_tones.append(t)
        st.session_state["selected_tones"] = selected_tones
    else:
        selected_tones = []
        st.session_state["selected_tones"] = []
    
    if len(selected_modes) == 1:
        if ui["words"] in selected_modes:
            count = len(df_hc_words[df_hc_words["类型"] == "单字"])
            st.caption(ui["char_count"].format(count))
        elif ui["phrases"] in selected_modes:
            count = len(df_hc_words[df_hc_words["类型"] == "词语"])
            st.caption(ui["phrase_count"].format(count))
        elif ui["sents"] in selected_modes:
            count = len(df_hc_sents)
            st.caption(ui["sent_count"].format(count))
    else:
        count_parts = []
        if ui["words"] in selected_modes:
            count = len(df_hc_words[df_hc_words["类型"] == "单字"])
            count_parts.append(ui["char_count"].format(count))
        if ui["phrases"] in selected_modes:
            count = len(df_hc_words[df_hc_words["类型"] == "词语"])
            count_parts.append(ui["phrase_count"].format(count))
        if ui["sents"] in selected_modes:
            count = len(df_hc_sents)
            count_parts.append(ui["sent_count"].format(count))
        st.caption(" | ".join(count_parts))

    filtered_df = current_df.copy()

    if search_type == ui["hanzi_search"]:
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

                match_info[idx] = score

            filtered_df = filtered_df[mask]
            if not filtered_df.empty:
                filtered_df['_type_priority'] = filtered_df.apply(get_entry_type_priority, axis=1)
                filtered_df['_match_score'] = filtered_df.index.map(lambda x: match_info.get(x, 0))
                filtered_df = filtered_df.sort_values(['_type_priority', '_match_score'], ascending=[True, False])
                filtered_df = filtered_df.drop(['_type_priority', '_match_score'], axis=1)
    else:
        filtered_df = filter_by_pinyin(filtered_df, search_query, selected_tones)

    st.subheader(ui["result_title"])
    
    if filtered_df.empty:
        st.caption(ui["entry_count"].format(0))
        st.info(ui["no_data"])
    else:
        st.caption(ui["entry_count"].format(len(filtered_df)))
        for _, row in filtered_df.iterrows():
            row = row.fillna("")
            word_to_show = row[char_col] if (char_col in row and row[char_col]) else row.get('普通话', '')
            display_title = f"{word_to_show}"
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
                    if "读法类型" in row and row["读法类型"]:
                        st.markdown(f"**读法类型:** {row['读法类型']}")
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
