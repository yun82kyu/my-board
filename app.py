import streamlit as st
import json
from github import Github
# 분리된 파일에서 관리 함수 불러오기
from category_manager import show_category_manager

# --- 1. GitHub 보안 설정 및 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 설정 확인 필요: {e}")
    st.stop()

# --- 2. 데이터 로드/저장 함수 ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        if "categories" in file_name:
            return ["기본분류"], None
        return [], None

def save_json(file_name, data_to_save, sha):
    json_string = json.dumps(data_to_save, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear()

# --- 3. 기본 페이지 설정 및 데이터 준비 ---
st.set_page_config(page_title="My Admin Board", layout="wide")

categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태 초기화
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 4. 좌측 사이드바 내비게이션 ---
with st.sidebar:
    st.title("🚀 Navigation")
    st.subheader("📁 카테고리")
    
    for idx, cat in enumerate(categories):
        # 사이드바 전용 키(sidebar_nav_) 부여하여 충돌 방지
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode == "list")
        if st.button(cat, key=f"sidebar_nav_{idx}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.query_params.clear()
            st.rerun()
            
    st.divider()
    # 관리 페이지 버튼
    if st.button("⚙️ 대분류 관리 센터", key="sidebar_manage_btn", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 5. 화면 분기 로직 ---

# [A] 대분류 관리 모드 (category_manager.py 실행)
if st.session_state.view_mode == "manage":
    # 관리 페이지 표시
    show_category_manager(categories, cat_sha, all_data, save_json)
    # 🌟 0순위 중요: 관리 모드일 때는 아래의 게시판 코드를 읽지 못하게 물리적 차단
    st.stop() 

# [B] 상세 보기 모드 (URL 파라미터 기반)
params = st.query_params
if params.get("view") == "detail":
    selected_no = params.get("no")
    post = next((i for i in all_data if str(i['no'])
