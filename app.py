import os
import re
from google import genai
import pandas as pd
import streamlit as st

st.set_page_config(page_title="公共工程品管刷題教練", page_icon="📚", layout="centered")

# 初始化 Gemini API 客戶端
# 優先讀取 Streamlit Secrets，如果沒有則讀取環境變數
api_key = None
try:
  if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
  pass

if not api_key:
  api_key = os.environ.get("GEMINI_API_KEY")

client = None
if api_key:
  try:
    client = genai.Client(api_key=api_key)
  except Exception as e:
    st.sidebar.error(f"⚠️ Gemini 初始化失敗: {e}")

st.title("🏗️ 公共工程品管刷題教練 (AI 家教版)")


@st.cache_data
def get_available_units():
  files = [f for f in os.listdir(".") if f.endswith(".xlsx")]
  files.sort()
  return files


unit_files = get_available_units()

if not unit_files:
  st.error("⚠️ 找不到任何 Excel 題庫檔案！")
  st.stop()

st.sidebar.header("📋 學習控制面板")
selected_unit = st.sidebar.selectbox("選擇練習單元", unit_files)


@st.cache_data
def load_data(file_name):
  df = pd.read_excel(file_name)
  return df


try:
  df = load_data(selected_unit)
except Exception as e:
  st.error(f"⚠️ 讀取檔案失敗：{e}")
  st.stop()

# 當切換單元時重置狀態
if "last_selected_unit" not in st.session_state:
  st.session_state.last_selected_unit = selected_unit

if st.session_state.last_selected_unit != selected_unit:
  st.session_state.current_index = 0
  st.session_state.show_answer = False
  st.session_state.ai_explanation = ""
  st.session_state.starred_questions = []
  st.session_state.last_selected_unit = selected_unit
  st.rerun()

if "current_index" not in st.session_state:
  st.session_state.current_index = 0
if "starred_questions" not in st.session_state:
  st.session_state.starred_questions = []
if "show_answer" not in st.session_state:
  st.session_state.show_answer = False
if "ai_explanation" not in st.session_state:
  st.session_state.ai_explanation = ""

total_questions = len(df)

if st.sidebar.button("🔄 重置目前單元進度"):
  st.session_state.current_index = 0
  st.session_state.show_answer = False
  st.session_state.ai_explanation = ""
  st.rerun()

st.sidebar.markdown(f"**當前單元總題數：** {total_questions} 題")
st.sidebar.markdown(
    f"**★ 本單元星號題：** {len(st.session_state.starred_questions)} 題"
)

if st.session_state.current_index >= total_questions:
  st.session_state.current_index = 0

idx = st.session_state.current_index
row = df.iloc[idx]

st.subheader(f"📖 單元：{selected_unit.replace('.xlsx', '')}")
st.markdown(f"### 第 {idx + 1} 題 / 共 {total_questions} 題")


def get_col_val(row_data, possible_names, default=""):
  for name in possible_names:
    if name in row_data and pd.notna(row_data[name]):
      return row_data[name]
  return default


full_text = str(
    get_col_val(row, ["題目", "問題", "Question", "題型"], "找不到題目欄位")
)


def parse_question_and_options(text):
  match = re.search(r"\(?[A-Da-d]\)", text)
  if not match:
    return text, []

  start_idx = match.start()
  question_title = text[:start_idx].strip()
  options_text = text[start_idx:]

  raw_options = re.findall(
      r"(\(?[A-Da-d]\)[^()]+?(?=\(?[A-Da-d]\)|$))", options_text
  )
  if not raw_options:
    raw_options = [
        o.strip()
        for o in re.split(r"\(?[A-Da-d]\)", options_text)
        if o.strip()
    ]

  return question_title, [o.strip() for o in raw_options if o.strip()]


q_title, extracted_options = parse_question_and_options(full_text)

st.write(f"**題目：** {q_title}")

options = (
    extracted_options if extracted_options else ["選項解析中或格式需確認"]
)

user_choice = st.radio(
    "請選擇答案：", options, key=f"q_{selected_unit}_{idx}", index=None
)

col1, col2 = st.columns(2)

with col1:
  if st.button("📤 送出答案"):
    if user_choice is not None:
      st.session_state.show_answer = True
      st.session_state.ai_explanation = ""
    else:
      st.warning("⚠️ 請先選擇一個選項！")

with col2:
  is_starred = idx in st.session_state.starred_questions
  star_btn_text = "★ 取消星號" if is_starred else "☆ 標記星號 (不確定)"
  if st.button(star_btn_text):
    if is_starred:
      st.session_state.starred_questions.remove(idx)
    else:
      st.session_state.starred_questions.append(idx)
    st.rerun()

if st.session_state.show_answer:
  ans = str(
      get_col_val(
          row,
          [
              "答案",
              "正確答案",
              "解答",
              "Ans",
              "參考答案",
              "正確解答",
              "答案選項",
          ],
          "無",
      )
  )
  exp = str(
      get_col_val(
          row,
          [
              "解析",
              "詳解",
              "說明",
              "Explanation",
              "解說",
              "考點說明",
              "備註",
          ],
          "",
      )
  )

  st.info(f"💡 **參考答案：** {ans}")
  if exp and exp != "nan":
    st.success(f"📖 **原題庫解析：**\n\n{exp}")

  st.markdown("---")
  st.markdown("### 🤖 Gemini AI 智慧家教解析")

  if not client:
    st.error(
        "⚠️ 尚未偵測到 Gemini API Key，請至 Streamlit Cloud Secrets"
        " 進行設定。"
    )
  else:
    if not st.session_state.ai_explanation:
      if st.button("✨ 產生存疑解析 / 為什麼選這題？"):
        with st.spinner(
            "Gemini 正在為你調閱法規與工程實務進行深度剖析中..."
        ):
          try:
            prompt = f"""
                        你是一位專業的公共工程品管與法規專家家教。
                        請針對以下公共工程品管題目進行詳細解說：
                        
                        題目：{q_title}
                        選項：
                        {chr(10).join(options)}
                        
                        原題庫參考答案：{ans}
                        原題庫解析：{exp}
                        
                        請用繁體中文回答，包含以下結構：
                        1. **正確選項與核心觀念**：明確指出正確答案為何。
                        2. **選項剖析**：解釋為什麼正確答案是對的，以及其他選項為什麼是錯的。
                        3. **法規或實務依據**：結合公共工程品質管理、採購法或工程實務說明背後原理。
                        """
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            st.session_state.ai_explanation = response.text
          except Exception as e:
            st.session_state.ai_explanation = f"⚠️ AI 解析生成失敗：{e}"
        st.rerun()

    if st.session_state.ai_explanation:
      st.markdown(st.session_state.ai_explanation)

  if st.button("下一題 ➡️"):
    if st.session_state.current_index < total_questions - 1:
      st.session_state.current_index += 1
      st.session_state.show_answer = False
      st.session_state.ai_explanation = ""
      st.rerun()
    else:
      st.balloons()
      st.success("🎉 太棒了！你已經把這個單元的題目全部刷完囉！")
