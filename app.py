import streamlit as st
import json
from github import Github

# --- 1. 기본 연결 및 데이터 처리 (생략 없이 유지) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

@st.cache_data(show_spinner=False)
def load_json(file_name):
    content = repo.get_contents(file_name)
    return json.loads(content.decoded_content.decode("utf-8")), content.sha

def save_json(file_name, data, sha):
    repo.update_file(file_name, "Update", json.dumps(data, indent=4, ensure_ascii=False), sha)
    st.cache_data.clear()

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="Admin Panel", layout="wide")

# 카테고리 로드
categories, cat_sha = load_json("categories.json")

# --- 3. 좌측 사이드바 (리스트 및 추가 기능) ---
with st.sidebar:
    # 대분류 글자와 + 버튼을 한 줄에 배치
    side_head_col1, side_head_col2 = st.columns([3, 1])
    with side_head_col1:
        st.subheader("📁 대분류")
    with side_head_col2:
        # + 버튼을 누르면 입력창이 나오고, 추가 후 rerun으로 팝업을 닫음
        with st.popover("➕"):
            new_cat = st.text_input("새 분류명", key="new_cat_input")
            if st.button("추가", use_container_width=True):
                if new_cat and new_cat not in categories:
                    categories.append(new_cat)
                    save_json("categories.json", categories, cat_sha)
                    # 추가 성공 시 세션 상태에 메시지를 남기거나 즉시 리런
                    st.success("추가됨!")
                    st.rerun()  # 이 코드가 실행되면 팝업이 닫히고 처음 화면으로 돌아갑니다.

    st.divider()

    # 현재 선택된 카테고리 확인 (없으면 첫 번째 것으로 설정)
    if "current_cat" not in st.session_state:
        st.session_state.current_cat = categories[0]

    # 카테고리 리스트를 버튼 형태로 나열
    for cat in categories:
        is_selected = (st.session_state.current_cat == cat)
        btn_style = "primary" if is_selected else "secondary"
        
        if st.button(cat, key=f"btn_{cat}", use_container_width=True, type=btn_style):
            st.session_state.current_cat = cat
            st.query_params.clear() # 상세페이지 보고 있었다면 목록으로 이동
            st.rerun()

# --- 4. 메인 화면 (임시 표시) ---
current_cat = st.session_state.current_cat
st.title(f"👤 {current_cat}")
st.write("사이드바에서 분류를 추가하고 선택해 보세요. 추가 버튼을 누르면 팝업이 자동으로 닫힙니다.")
