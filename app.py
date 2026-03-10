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

# --- 3. 기본 페이지 설정 ---
st.set_page_config(page_title="Admin Board", layout="wide")

categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태 초기화
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 4. 좌측 사이드바 ---
with st.sidebar:
    st.title("🚀 Navigation")
    st.subheader("📁 카테고리")
    
    for idx, cat in enumerate(categories):
        # 사이드바 전용 키(sb_nav_) 사용하여 메인 버튼과 격리
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode == "list")
        if st.button(cat, key=f"sb_nav_{idx}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.query_params.clear()
            st.rerun()
            
    st.divider()
    # 관리 페이지 진입 버튼
    if st.button("⚙️ 대분류 관리 센터", key="sb_manage_admin", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 5. 화면 분기 로직 ---

# [CASE A] 대분류 관리 모드
if st.session_state.view_mode == "manage":
    # 관리 함수 호출
    show_category_manager(categories, cat_sha, all_data, save_json)
    # 아래 게시판 코드가 실행되지 않도록 물리적 차단 (에러 방지 핵심)
    st.stop() 

# [CASE B] 상세 보기 모드
params = st.query_params
if params.get("view") == "detail":
    selected_no = params.get("no")
    post = next((i for i in all_data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록으로", key="back_to_list_btn"): 
            st.query_params.clear()
            st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    st.stop()

# [CASE C] 일반 목록 모드
st.title(f"👤 {st.session_state.current_cat}")
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# 상단 검색 및 추가
search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", key="main_search", label_visibility="collapsed")

if write_c.button("📝 새 행 추가", key="main_add_row", use_container_width=True):
    st.session_state.show_editor = not st.session_state.get("show_editor", False)

if st.session_state.get("show_editor", False):
    with st.form("main_write_form"): # 메인 페이지의 폼은 단일 파일 내에 있어 안전함
        nt = st.text_input("제목")
        nc = st.text_area("내용")
        if st.form_submit_button("저장하기"):
            if nt and nc:
                new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {"no": new_no, "title": nt, "name": "관리자", "content": nc, "category": st.session_state.current_cat})
                save_json("data.json", all_data, data_sha)
                st.session_state.show_editor = False
                st.rerun()

st.write("")
# 목록 헤더
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

for item in filtered_data:
    if search_q and search_q.lower() not in item['title'].lower(): continue
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    if c2.button(item['title'], key=f"post_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
    c3.write(item.get('name', '관리자'))
    if c4.button("🗑️", key=f"del_{item['no']}"):
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha)
        st.rerun()
