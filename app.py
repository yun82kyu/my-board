import streamlit as st
import json
from github import Github

# --- 1. 보안 설정 및 GitHub 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# 데이터 로드 함수
def load_data():
    file_content = repo.get_contents("data.json")
    return json.loads(file_content.decoded_content.decode("utf-8")), file_content.sha

# 데이터 저장 함수
def save_data(data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file("data.json", "Update board data", json_string, sha)

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="LLM Study Admin", layout="wide")

# 세션 상태 초기화 (상세 페이지 이동용)
if "view" not in st.session_state:
    st.session_state.view = "list"
if "selected_post" not in st.session_state:
    st.session_state.selected_post = None

# --- 3. UI 로직 ---

# A. 상세 페이지 화면
if st.session_state.view == "detail":
    post = st.session_state.selected_post
    st.button("⬅️ 목록으로 돌아가기", on_click=lambda: setattr(st.session_state, "view", "list"))
    st.divider()
    st.title(f"📖 {post['title']}")
    st.caption(f"번호: {post['no']} | 작성자: {post['name']}")
    st.info(post['content'])
    st.divider()

# B. 메인 목록 및 새 글 추가 화면
else:
    st.title("🚀 LLM 관리자 자동 게시판")
    
    data, sha = load_data()

    # --- 새 글 추가 섹션 (행 추가 레이아웃) ---
    with st.expander("➕ 새 게시글 추가하기 (클릭해서 행 추가)", expanded=False):
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                new_no = st.number_input("번호", value=max([int(i['no']) for i in data]) + 1 if data else 1)
            with col2:
                new_title = st.text_input("제목을 입력하세요")
            new_content = st.text_area("내용을 입력하세요")
            
            submit = st.form_submit_button("게시글 행 추가")
            if submit:
                if new_title and new_content:
                    new_post = {"no": new_no, "title": new_title, "name": "관리자", "content": new_content, "viewcnt": 0}
                    data.insert(0, new_post)
                    save_data(data, sha)
                    st.success("새 행이 추가되었습니다! 깃허브 반영 중...")
                    st.rerun()
                else:
                    st.warning("제목과 내용을 입력해주세요.")

    st.divider()

    # --- 목록 테이블 섹션 ---
    st.subheader("📋 게시글 목록")
    # 테이블 헤더
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 5, 2, 1])
    h_col1.write("**No**")
    h_col2.write("**제목 (클릭시 상세페이지)**")
    h_col3.write("**작성자**")
    h_col4.write("**관리**")
    st.divider()

    # 데이터 출력
    for idx, item in enumerate(data):
        c1, c2, c3, c4 = st.columns([1, 5, 2, 1])
        c1.write(item['no'])
        
        # 제목을 클릭하면 상세페이지로 이동하도록 세션 상태 변경
        if c2.button(item['title'], key=f"btn_{idx}", use_container_width=True):
            st.session_state.selected_post = item
            st.session_state.view = "detail"
            st.rerun()
            
        c3.write(item['name'])
        
        if c4.button("🗑️", key=f"del_{idx}"):
            data.pop(idx)
            save_data(data, sha)
            st.rerun()
