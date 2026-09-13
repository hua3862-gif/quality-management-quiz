import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="公共工程品管刷題教練", page_icon="📚", layout="centered")

st.title("🏗️ 公共工程品管刷題教練")


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
  st.session_state.starred_questions = []
  st.session_state.last_selected_unit = selected_unit
  st.rerun()

if "current_index" not in st.session_state:
  st.session_state.current_index = 0
if "starred_questions" not in st.session_state:
  st.session_state.starred_questions = []
if "show_answer" not in st.session_state:
  st.session_state.show_answer = False

total_questions = len(df)

if st.sidebar.button("🔄 重置目前單元進度"):
  st.session_state.current_index = 0
  st.session_state.show_answer = False
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


q_text = get_col_val(
  row, ["題目", "問題", "Question", "題型"], "找不到題目欄位"
)
st.write(f"**題目：** {q_text}")

# 自動尋找所有可能的選項欄位
options = []
# 排除掉題目、答案、解析等欄位後，其他有內容的欄位都當作選項
exclude_cols = [
  "題目",
  "問題",
  "Question",
  "答案",
  "正確答案",
  "Ans",
  "解析",
  "說明",
  "Explanation",
]
for col in df.columns:
  if col not in exclude_cols:
    val = row[col]
    if pd.notna(val) and str(val).strip() != "":
      options.append(f"{col}: {val}" if not col.startswith("選項") else f"{val}")

user_choice = st.radio(
  "請選擇答案：", options, key=f"q_{selected_unit}_{idx}", index=None
)

col1, col2 = st.columns(2)

with col1:
  if st.button("📤 送出答案"):
    if user_choice is not None:
      st.session_state.show_answer = True
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
  ans = get_col_val(row, ["答案", "正確答案", "Ans"], "無")
  exp = get_col_val(row, ["解析", "說明", "Explanation"], "無解析")
  st.info(f"💡 **正確答案：** {ans}")
  st.success(f"📖 **解析：** {exp}")

  if st.button("下一題 ➡️"):
    if st.session_state.current_index < total_questions - 1:
      st.session_state.current_index += 1
      st.session_state.show_answer = False
      st.rerun()
    else:
      st.balloons()
      st.success("🎉 太棒了！你已經把這個單元的題目全部刷完囉！")
