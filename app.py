import streamlit as st
import json
from github import Github
# 분리한 파일 불러오기
from category_manager import show_category_manager

# --- 기본 설정 및 데이터 로드 (생략/기존동일) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except:
    st.error("GitHub 설정 확인 필요")
    st.stop()

@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return ([] if "data" in file_name else ["기본분류"]), None

def save_json(file_name, data_to_save, sha):
    json_string = json.dumps(data_to_save, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update", json_string, sha)
    st.cache_data.clear()

st.set_page_config(page_title="My Board", layout="wide")
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
if "current_cat" not in st.session_state: st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 사이드바 ---
with st.sidebar:
    st.title("🚀 Nav")
    for idx, cat in enumerate(categories):
        if st.button(cat, key=f"nav_{idx}", use_container_width=True, 
                     type="primary" if (st.session_state.current_cat == cat and st.session_state.view_mode == "list") else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.rerun()
    st.divider()
    if st.button("⚙️ 대분류 관리", use_container_width=True, type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 메인 로직 분기 ---
if st.session_state.view_mode == "manage":
    # 분리된 파일의 함수 호출!
    show_category_manager(categories, cat_sha, all_data, save_json)
else:
    # 메인 게시판 목록 출력 (기존 로직)
    st.title(f"👤 {st.session_state.current_cat}")
    # ... (필터링 및 목록 출력 코드 생략)
