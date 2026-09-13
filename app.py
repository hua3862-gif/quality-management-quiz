import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="公共工程品管刷題教練", page_icon="📚", layout="centered")

st.title("🏗️ 公共工程品管刷題教練")


# 自動掃描專案資料夾裡所有 .xlsx 檔案作為單元選項
@st.cache_data
def get_available_units():
  files = [f for f in os.listdir(".") if f.endswith(".xlsx")]
  # 排序讓檔名整齊
  files.sort()
  return files


unit_files = get_available_units()

if not unit_files:
  st.error(
    "⚠️ 找不到任何 Excel 題庫檔案！請確認是否已將單元 Excel 檔案上傳至此 GitHub"
    " 專案中。"
  )
  st.stop()

# 側邊欄：單元下拉選單
st.sidebar.header("📋 學習控制面板")

# 讓使用者選擇單元
selected_unit = st.sidebar.selectbox("選擇練習單元", unit_files)


# 根據選取的單元動態載入對應的 Excel
@st.cache_data
def load_data(file_name):
  df = pd.read_excel(file_name)
  return df


try:
  df = load_data(selected_unit)
except Exception as e:
  st.error(f"⚠️ 讀取檔案 {selected_unit} 失敗！錯誤訊息: {e}")
  st.stop()

# 當切換單元時，重置題目索引與狀態
if "last_selected_unit" not in st.session_state:
  st.session_state.last_selected_unit = selected_unit

if st.session_state.last_selected_unit != selected_unit:
  st.session_state.current_index = 0
  st.session_state.show_answer = False
  st.session_state.starred_questions = []
  st.session_state.last_selected_unit = selected_unit
  st.rerun()

# 初始化 Session State
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

# 確保索引不會超出範圍
if st.session_state.current_index >= total_questions:
  st.session_state.current_index = 0

# 顯示當前題目
idx = st.session_state.current_index
row = df.iloc[idx]

st.subheader(f"📖 單元：{selected_unit.replace('.xlsx', '')}")
st.markdown(f"### 第 {idx + 1} 題 / 共 {total_questions} 題")
st.write(f"**題目：** {row['題目']}")

# 選項
options = [row["選項A"], row["選項B"], row["選項C"], row["選項D"]]

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

# 顯示解析
if st.session_state.show_answer:
  st.info(f"💡 **正確答案：** {row['答案']}")
  st.success(f"📖 **解析：** {row['解析']}")

  if st.button("下一題 ➡️"):
    if st.session_state.current_index < total_questions - 1:
      st.session_state.current_index += 1
      st.session_state.show_answer = False
      st.rerun()
    else:
      st.balloons()
      st.success("🎉 太棒了！你已經把這個單元的題目全部刷完囉！")
