import streamlit as st
import json
import time
from github import Github

# --- 1. GitHub 설정 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 설정 오류: {e}")
    st.stop()

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

# --- 2. 초기화 ---
st.set_page_config(page_title="Admin Board", layout="wide")

# 데이터 로드
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
if "current_cat" not in st.session_state: st.session_state.current_cat = categories[0]
# 삭제 실행 신호를 저장할 변수
if "trigger_delete" not in st.session_state: st.session_state.trigger_delete = False

# --- 3. 사이드바 ---
with st.sidebar:
    st.title("🚀 Navigation")
    for idx, cat in enumerate(categories):
        # 고정된 유니크 키 사용 (cat 이름 포함)
        if st.button(f"📁 {cat}", key=f"sb_nav_{cat}_{idx}", use_container_width=True):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.rerun()
    st.divider()
    if st.button("⚙️ 관리 센터", key="sb_admin_btn", use_container_width=True):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 4. 화면 분기 ---

if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    
    # [추가 섹션]
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", key="m_add_input")
        if st.button("추가하기", key="m_add_confirm_btn", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json("categories.json", categories, cat_sha)
                st.rerun()

    # [삭제 섹션 - 에러 방지 구조]
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        deletable = [c for c in categories if len([i for i in all_data if i.get('category') == c]) == 0]
        
        if not deletable:
            st.info("비어 있는 분류가 없습니다.")
        else:
            # selectbox와 checkbox는 상태만 저장
            target = st.selectbox("삭제할 분류", deletable, key="m_del_target_select", index=None)
            confirm = st.checkbox("정말로 삭제하시겠습니까?", key="m_del_confirm_check")
            
            # 🔥 핵심: 버튼 클릭 시 즉시 실행하지 않고 '신호'만 세션에 저장
            if st.button("🔥 선택 분류 삭제 실행", key="m_del_final_btn", type="danger", use_container_width=True):
                if target and confirm:
                    st.session_state.target_to_del = target
                    st.session_state.trigger_delete = True
                    st.rerun() # 신호를 가지고 리런
                elif not confirm:
                    st.warning("체크박스를 선택하세요.")

    # 🌟 실제 데이터 처리는 모든 위젯 코드가 끝난 뒤에 수행 (에러 방지 치트키)
    if st.session_state.get("trigger_delete"):
        target = st.session_state.target_to_del
        if target in categories:
            categories.remove(target)
            save_json("categories.json", categories, cat_sha)
            if st.session_state.current_cat == target:
                st.session_state.current_cat = categories[0]
        st.session_state.trigger_delete = False # 신호 초기화
        st.rerun()

    if st.button("⬅️ 돌아가기", key="m_back_btn"):
        st.session_state.view_mode = "list"
        st.rerun()
    st.stop() # 관리 모드 종료

# --- 게시판 목록 모드 ---
st.title(f"👤 {st.session_state.current_cat}")
# ... (게시판 목록 코드 생략 - 기존과 동일하게 작성하되 key만 겹치지 않게 유지)
