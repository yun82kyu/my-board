import streamlit as st
import json
from github import Github

# --- 1. 기본 연결 설정 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# JSON 로드/저장 함수
def load_json(file_name):
    content = repo.get_contents(file_name)
    return json.loads(content.decoded_content.decode("utf-8")), content.sha

def save_json(file_name, data, sha):
    repo.update_file(file_name, "Update", json.dumps(data, indent=4, ensure_ascii=False), sha)
    st.cache_data.clear()

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="Admin Panel", layout="wide")

# 카테고리 불러오기
categories, cat_sha = load_json("categories.json")

# --- 3. 좌측 사이드바 (리스트 형태) ---
with st.sidebar:
    # 대분류 글자와 추가 버튼을 한 줄에 배치
    side_col1, side_col2 = st.columns([3, 1])
    with side_col1:
        st.subheader("📁 대분류")
    with side_col2:
        # 팝업(popover) 형태로 추가 버튼 배치
        with st.popover("➕"):
            new_cat = st.text_input("분류명")
            if st.button("추가"):
                if new_cat and new_cat not in categories:
                    categories.append(new_cat)
                    save_json("categories.json", categories, cat_sha)
                    st.rerun()

    st.divider()

    # 콤보박스 대신 버튼 리스트로 카테고리 나열
    selected_cat = st.session_state.get("current_cat", categories[0])
    
    for cat in categories:
        # 선택된 카테고리는 강조(primary), 나머지는 기본(secondary)
        btn_type = "primary" if selected_cat == cat else "secondary"
        if st.button(cat, key=f"side_{cat}", use_container_width=True, type=btn_type):
            st.session_state.current_cat = cat
            st.query_params.clear() # 주소창 초기화 (목록으로 돌아가기 효과)
            st.rerun()

# --- 4. 메인 화면 (현재 선택된 카테고리 표시) ---
# 세션에 저장된 현재 카테고리 가져오기
current_cat = st.session_state.get("current_cat", categories[0])
st.title(f"👤 {current_cat}")

st.write("선택하신 대분류의 목록이 여기에 표시됩니다. (다음 단계에서 목록/검색 구현)")
