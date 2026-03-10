import streamlit as st
import json
from github import Github
from datetime import datetime
import time

st.set_page_config(page_title="My Board", layout="wide")

# --- GitHub & Data Load (기존 로직 유지) ---
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
except Exception as e:
    st.error(f"GitHub 연결 실패: {e}"); st.stop()

@st.cache_data(show_spinner=False)
def load_json(file):
    try:
        content = repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except: return [], None

def save_json(file, data, sha=None):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        if not sha:
            try: sha = repo.get_contents(file).sha
            except: pass
        if sha: repo.update_file(file, f"update {file}", json_string, sha)
        else: repo.create_file(file, f"create {file}", json_string)
        st.cache_data.clear()
    except Exception as e: st.error(f"저장 실패: {e}")

categories, cat_sha = load_json("categories.json")
posts, data_sha = load_json("data.json")
if not categories: categories = ["기본분류"]; save_json("categories.json", categories)

# --- 세션 상태 확장 ---
if "mode" not in st.session_state: st.session_state.mode = "board"
if "category" not in st.session_state: st.session_state.category = categories[0]
if "view_post" not in st.session_state: st.session_state.view_post = None
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False # 수정 모드 추적
if "write_mode" not in st.session_state: st.session_state.write_mode = False # 글쓰기 모드 추적

t_key = str(int(time.time()))

# --- 사이드바 ---
with st.sidebar:
    st.title("📚 내 미니 보드")
    c1, c2 = st.columns(2)
    if c1.button("📋 게시판", key="nav_board", use_container_width=True):
        st.session_state.mode = "board"; st.session_state.view_post = None
        st.session_state.write_mode = False; st.rerun()
    if c2.button("⚙️ 관리", key="nav_admin", use_container_width=True):
        st.session_state.mode = "admin"; st.rerun()
    st.divider()
    st.subheader("📁 카테고리")
    for idx, c in enumerate(categories):
        if st.button(c, key=f"side_cat_{idx}_{t_key}", use_container_width=True, 
                     type="primary" if st.session_state.category == c else "secondary"):
            st.session_state.category = c; st.session_state.view_post = None
            st.session_state.write_mode = False; st.session_state.mode = "board"; st.rerun()

# --- 관리자 모드 (기존 유지) ---
if st.session_state.mode == "admin":
    st.title("⚙️ 카테고리 관리")
    # ... (카테고리 추가/수정/삭제 로직 - 기존과 동일)
    # [생략: 기존 관리자 코드를 그대로 넣으시면 됩니다]

# --- 게시판 모드 ---
else:
    # 1. 글쓰기 화면 (Write Mode)
    if st.session_state.write_mode:
        st.title("📝 새 게시글 작성")
        with st.container(border=True):
            new_title = st.text_input("제목", placeholder="제목을 입력하세요")
            new_content = st.text_area("내용", height=300, placeholder="내용을 상세히 입력하세요")
            
            col_w1, col_w2 = st.columns([1, 1])
            if col_w1.button("💾 저장하기", use_container_width=True, type="primary"):
                if new_title and new_content:
                    new_no = max([p.get("no",0) for p in posts], default=0) + 1
                    posts.insert(0, {
                        "no": new_no, "title": new_title, "content": new_content,
                        "category": st.session_state.category, "views": 0,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_json("data.json", posts, data_sha)
                    st.session_state.write_mode = False; st.rerun()
                else: st.warning("제목과 내용을 모두 입력해주세요.")
            if col_w2.button("❌ 취소", use_container_width=True):
                st.session_state.write_mode = False; st.rerun()

    # 2. 글 수정 화면 (Edit Mode)
    elif st.session_state.edit_mode and st.session_state.view_post:
        post = next((x for x in posts if x["no"] == st.session_state.view_post), None)
        if post:
            st.title("✏️ 게시글 수정")
            with st.container(border=True):
                edit_title = st.text_input("제목", value=post["title"])
                edit_content = st.text_area("내용", value=post["content"], height=300)
                
                col_e1, col_e2 = st.columns(2)
                if col_e1.button("✅ 수정 완료", use_container_width=True, type="primary"):
                    post["title"] = edit_title
                    post["content"] = edit_content
                    save_json("data.json", posts, data_sha)
                    st.session_state.edit_mode = False; st.rerun()
                if col_e2.button("🔙 취소", use_container_width=True):
                    st.session_state.edit_mode = False; st.rerun()

    # 3. 기본 목록 및 상세 보기 화면
    else:
        st.title(f"📂 {st.session_state.category}")
        
        # 행 추가 버튼 (상단 배치)
        if st.button("➕ 새 게시글 추가", key="main_add_btn"):
            st.session_state.write_mode = True
            st.session_state.view_post = None
            st.rerun()

        st.divider()

        # 상세 보기 영역
        if st.session_state.view_post:
            post = next((x for x in posts if x["no"] == st.session_state.view_post), None)
            if post:
                with st.container(border=True):
                    col_h1, col_h2 = st.columns([8, 2])
                    col_h1.subheader(post["title"])
                    if col_h2.button("✏️ 수정하기", use_container_width=True):
                        st.session_state.edit_mode = True; st.rerun()
                    
                    st.caption(f"📅 {post['date']} | 👀 조회수 {post.get('views',0)}")
                    st.write(post["content"])
                    if st.button("✖️ 닫기"):
                        st.session_state.view_post = None; st.rerun()
                st.divider()

        # 목록 영역
        filtered = [p for p in posts if p.get("category") == st.session_state.category]
        if not filtered:
            st.info("게시글이 없습니다.")
        else:
            # 테이블 헤더 느낌의 컬럼
            h1, h2, h3 = st.columns([1, 7, 1.5])
            h1.markdown("**번호**")
            h2.markdown("**제목**")
            h3.markdown("**관리**")
            
            for p in filtered:
                col1, col2, col3 = st.columns([1, 7, 1.5])
                col1.write(f"{p['no']}")
                if col2.button(p["title"], key=f"list_{p['no']}_{t_key}", use_container_width=True):
                    st.session_state.view_post = p["no"]
                    p["views"] = p.get("views", 0) + 1
                    save_json("data.json", posts, data_sha); st.rerun()
                if col3.button("🗑️ 삭제", key=f"del_{p['no']}_{t_key}", use_container_width=True):
                    posts = [x for x in posts if x["no"] != p["no"]]
                    save_json("data.json", posts, data_sha); st.rerun()
