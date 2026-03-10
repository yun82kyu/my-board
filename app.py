import streamlit as st
import json
from github import Github
from category_manager import show_category_manager

# --- 1. 보안 및 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except:
    st.error("GitHub 설정 확인 필요")
    st.stop()

# --- 2. 데이터 함수 ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        if "categories" in file_name: return ["기본분류"], None
        return [], None

def save_json(file_name, data_to_save, sha):
    json_string = json.dumps(data_to_save, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update", json_string, sha)
    st.cache_data.clear()

# --- 3. 설정 ---
st.set_page_config(page_title="My Board", layout="wide")
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
if "current_cat" not in st.session_state: 
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 4. 사이드바 ---
with st.sidebar:
    st.title("🚀 Nav")
    for idx, cat in enumerate(categories):
        # 🌟 Key에 카테고리 이름과 고유 접두사를 붙여 중복 원천 차단
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode == "list")
        if st.button(f"📁 {cat}", key=f"sb_nav_btn_{cat}_{idx}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.query_params.clear()
            st.rerun()
            
    st.divider()
    if st.button("⚙️ 관리 센터", key="sb_admin_mode_btn", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 5. 화면 분기 ---
if st.session_state.view_mode == "manage":
    show_category_manager(categories, cat_sha, all_data, save_json)
    st.stop() # 관리 모드일 때 아래 코드 실행 금지

# [상세 보기]
params = st.query_params
if params.get("view") == "detail":
    post = next((i for i in all_data if str(i['no']) == str(params.get("no"))), None)
    if post:
        if st.button("⬅️ 목록", key="detail_back"): 
            st.query_params.clear()
            st.rerun()
        st.subheader(post['title'])
        st.write(post['content'])
    st.stop()

# [일반 목록]
st.title(f"👤 {st.session_state.current_cat}")
filtered = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# (목록 출력 부분 생략 - 기존과 동일하되 버튼 key만 중복 안되게 유지)
for item in filtered:
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    # 게시글 버튼 Key에 no 포함
    if c2.button(item['title'], key=f"main_post_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
    # 삭제 버튼 Key에 no 포함
    if c4.button("🗑️", key=f"main_del_{item['no']}"):
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha)
        st.rerun()
