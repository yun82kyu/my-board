import streamlit as st
import json
from github import Github

# --- 1. GitHub 연결 설정 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 연결 오류: {e}")
    st.stop()

# --- 2. 데이터 로드/저장 함수 ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        if "categories" in file_name: return ["기본분류"], None
        return [], None

def save_json(file_name, data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear()

# --- 3. 데이터 준비 및 세션 초기화 ---
st.set_page_config(page_title="My Board", layout="wide")

categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0]

# --- 4. 좌측 사이드바 ---
with st.sidebar:
    st.title("🚀 Navigation")
    
    if st.button("📋 게시판 보기", key="nav_list_btn", use_container_width=True, 
                 type="primary" if st.session_state.view_mode == "list" else "secondary"):
        st.session_state.view_mode = "list"
        st.rerun()
        
    if st.button("⚙️ 대분류 관리", key="nav_manage_btn", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()
    
    st.divider()
    
    if st.session_state.view_mode == "list":
        st.subheader("📁 카테고리")
        for idx, cat in enumerate(categories):
            is_active = (st.session_state.current_cat == cat)
            if st.button(cat, key=f"side_cat_{idx}", use_container_width=True, 
                         type="primary" if is_active else "secondary"):
                st.session_state.current_cat = cat
                st.rerun()

# --- 5. 메인 화면 분기 ---

# [A] 대분류 관리 페이지
if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    
    with st.container(border=True):
        st.subheader("➕ 새 분류 추가")
        new_cat = st.text_input("추가할 분류 이름을 입력하세요", key="input_new_cat")
        if st.button("추가하기", key="btn_add_cat", use_container_width=True):
            if new_cat and new_cat not in categories:
                categories.append(new_cat)
                save_json("categories.json", categories, cat_sha)
                st.success(f"'{new_cat}' 분류가 추가되었습니다!")
                st.rerun()
            elif new_cat in categories:
                st.warning("이미 존재하는 분류입니다.")

    st.write("")

    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        st.caption("※ 게시글이 하나도 없는 분류만 삭제할 수 있습니다.")
        
        deletable = [c for c in categories if len([i for i in all_data if i.get('category') == c]) == 0]
        
        if not deletable:
            st.info("삭제 가능한 빈 분류가 없습니다.")
        else:
            del_target = st.selectbox("삭제할 분류 선택", deletable, key="select_del_cat")
            confirm = st.checkbox("정말로 이 분류를 삭제하시겠습니까?", key="chk_del_confirm")
            
            if st.button("선택한 분류 삭제", key="btn_del_cat", type="danger", use_container_width=True):
                if confirm and del_target:
                    if len(categories) > 1:
                        categories.remove(del_target)
                        # --- 오류 수정 지점: 괄호를 정확히 닫음 ---
                        save_json("categories.json", categories, cat_sha)
                        if st.session_state.current_cat == del_target:
                            st.session_state.current_cat = categories[0]
                        st.rerun()
                    else:
                        st.error("최소 한 개의 분류는 남겨두어야 합니다.")
                else:
                    st.warning("삭제 확인 체크박스에 체크해 주세요.")

# [B] 게시판 목록 페이지
else:
    st.title(f"📍 {st.session_state.current_cat}")
    
    filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

    with st.expander(f"➕ {st.session_state.current_cat}에 새 글 쓰기"):
        with st.form("write_form"):
            title = st.text_input("제목")
            content = st.text_
