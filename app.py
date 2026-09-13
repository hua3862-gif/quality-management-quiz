import pandas as pd
import streamlit as st

st.set_page_config(page_title="公共工程品管刷題教練", page_icon="📚", layout="centered")

st.title("🏗️ 公共工程品管刷題教練")


# 載入題庫函數 (支援多個單元 Excel 或單一總檔)
@st.cache_data
def load_data():
  # 預設讀取 question_bank.xlsx，你之後也可以上傳多個檔案並在這裡調整
  df = pd.read_excel("question_bank.xlsx")
  return df


try:
  df = load_data()
except Exception as e:
  st.error(
    "⚠️ 讀取題庫失敗！請確認是否已將 'question_bank.xlsx' 上傳至此 GitHub"
    f" 專案中。\n錯誤訊息: {e}"
  )
  st.stop()

# 初始化 Session State (紀錄目前題號、星號題與答題狀態)
if "current_index" not in st.session_state:
  st.session_state.current_index = 0
if "starred_questions" not in st.session_state:
  st.session_state.starred_questions = []
if "show_answer" not in st.session_state:
  st.session_state.show_answer = False

total_questions = len(df)

# 側邊欄控制面板
st.sidebar.header("📋 控制面板")
if st.sidebar.button("🔄 重置進度到第一題"):
  st.session_state.current_index = 0
  st.session_state.show_answer = False
  st.rerun()

st.sidebar.markdown(f"**總題數：** {total_questions} 題")
st.sidebar.markdown(
  f"**★ 星號不確定題：** {len(st.session_state.starred_questions)} 題"
)

# 顯示當前題目
idx = st.session_state.current_index
row = df.iloc[idx]

st.subheader(f"第 {idx + 1} 題 / 共 {total_questions} 題")
st.write(f"**題目：** {row['題目']}")

# 選項
options = [row["選項A"], row["選項B"], row["選項C"], row["選項D"]]

user_choice = st.radio(
  "請選擇答案：", options, key=f"q_{idx}", index=None
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
