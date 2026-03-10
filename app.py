import streamlit as st
import json
from github import Github
from category_manager import show_category_manager

# --- 1. GitHub 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except:
    st.error("GitHub 설정 오류")
    st.stop()

# --- 2. 데이터 함수 ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return (["기본분류"], None) if "cat" in file_name else ([], None)

def save_json(file_name, data, sha):
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update", json_str, sha)
    st.cache_data.clear()

# --- 3. 기본 설정 ---
st.set_page_config(page_title="My Admin Board", layout="wide")
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
if "current_cat" not in st.session_state: st.session_state.current_cat = categories[0]

# --- 4. 사이드바 (키 중복 방지 강화) ---
with st.sidebar:
    st.title("🚀 Navigation")
    for idx, cat in enumerate(categories):
        # 키값에 카테고리 명을 포함하여 중복 원천 차단
        btn_key = f"sb_btn_{cat}_{idx}"
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode == "list")
        if st.button(cat, key=btn_key, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.rerun()
    
    st.divider()
    if st.button("⚙️ 관리 센터", key="sb_admin_go", use_container_width=True):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 5. 화면 분기 ---
if st.session_state.view_mode == "manage":
    # 관리 함수 호출
    show_category_manager(categories, cat_sha, all_data, save_json)
    # 아래 코드가 실행되지 않도록 물리적 차단
    st.stop()

# [목록 모드]
st.title(f"👤 {st.session_state.current_cat}")
# ... (게시판 목록 코드 생략 - 기존과 동일)
