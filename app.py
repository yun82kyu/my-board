import streamlit as st
import json
from github import Github
from datetime import datetime
import time

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# GitHub 연결
# -----------------------------
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
except Exception as e:
    st.error(f"GitHub 연결 실패: {e}")
    st.stop()

# -----------------------------
# 데이터 로드/저장
# -----------------------------
@st.cache_data(show_spinner=False)
def load_json(file):
    try:
        content = repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

def save_json(file, data, sha=None):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        if sha is None:
            try:
                curr_content = repo.get_contents(file)
                sha = curr_content.sha
            except: pass
        
        if sha:
            repo.update_file(file, f"update {file}", json_string, sha)
        else:
            repo.create_file(file, f"create {file}", json_string)
        
        st.cache_data.clear()
    except Exception as e:
        st.error(f"저장 실패: {e}")

# 데이터 초기화
categories, cat_sha = load_json("categories.json")
posts, data_sha = load_json("data.json")

if not categories:
    categories = ["기본분류"]
    save_json("categories.json", categories)

# -----------------------------
# 세션 상태
# -----------------------------
if "mode" not in st.session_state: st.session_state.mode = "board"
if "category" not in st.session_state: st.session_state.category = categories[0]
if "view_post" not in st.session_state: st.session_state.view_post = None
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

t_key = str(int(time.time()))

# -----------------------------
# 사이드바 (기능 통합 유지)
# -----------------------------
with st.sidebar:
    st.title("📚 내 미니 보드")
    
    col_n1, col_n2 = st.columns(2)
    if col_n1.button("📋 게시판", key="nav_board", use_container_width=True):
        st.session_state.mode = "board"
        st.session_state.view_post = None
        st.session_state.write_mode = False
        st.rerun()
    if col_n2.button("⚙️ 관리", key="nav_admin", use_container_width=True):
        st.session_state.mode = "admin"
        st.rerun()

    st.divider()
    st.subheader("📁 카테고리 목록")
    for idx, c in enumerate(categories):
        is_active = (st.session_state.category == c)
        if st.button(c, key=f"side_cat_{idx}_{t_key}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.category = c
            st.session_state.view_post = None
            st.session_state.write_mode = False
            st.session_state.mode = "board"
            st.rerun()

# -----------------------------
# [A] 관리자 모드 (기본 소스 유지)
# -----------------------------
if st.session_state.mode == "admin":
    st.title("⚙️ 카테고리 관리")

    with st.container(border=True):
        st.subheader("➕ 추가")
        new_cat = st.text_input("새 카테고리 이름", key="admin_add_in")
        if st.button("카테고리 추가 실행", key="admin_add_btn"):
            if new_cat and new_cat not in categories:
                categories.append(new_cat)
                save_json("categories.json", categories, cat_sha)
                st.rerun()

    with st.container(border=True):
        st.subheader("✏️ 수정")
        edit_target = st.selectbox("수정할 대상", categories, key="admin_edit_sel")
        new_name = st.text_input("변경할 이름", key="admin_edit_in")
        if st.button("이름 변경 실행", key="admin_edit_btn"):
            if new_name and new_name != edit_target:
                idx = categories.index(edit_target)
                categories[idx] = new_name
                for p in posts:
                    if p.get("category") == edit_target: p["category"] = new_name
                save_json("categories.json", categories, cat_sha)
                save_json("data.json", posts, data_sha)
                st.rerun()

    with st.container(border=True):
        st.subheader("🗑️ 삭제")
        del_target = st.selectbox("삭제할 대상", categories, key="admin_del_sel")
        if st.button("카테고리 삭제 실행", key="admin_del_btn"):
            count = len([p for p in posts if p.get("category") == del_target])
            if count > 0:
                st.error(f"'{del_target}'에 {count}개의 글이 있어 삭제할 수 없습니다.")
            elif len(categories) <= 1:
                st.error("최소 한 개의 카테고리가 필요합니다.")
            else:
                categories.remove(del_target)
                save_json("categories.json", categories, cat_sha)
                st.rerun()

# -----------------------------
# [B] 게시판 모드 (글쓰기/수정/목록)
# -----------------------------
else:
    # 1. 글쓰기 페이지
    if st.session_state.write_mode:
        st.title("📝 새 게시글 작성")
        with st.container(border=True):
            w_title = st.text_input("제목")
            w_content = st.text_area("내용", height=400)
            c1, c2 = st.columns(2)
            if c1.button("💾 저장", use_container_width=True, type="primary"):
                if w_title and w_content:
                    new_no = max([p.get("no",0) for p in posts], default=0) + 1
                    posts.insert(0, {
                        "no": new_no, "title": w_title, "content": w_content,
                        "category": st.session_state.category, "views": 0,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_json("data.json", posts, data_sha)
                    st.session_state.write_mode = False
                    st.rerun()
            if c2.button("❌ 취소", use_container_width=True):
                st.session_state.write_mode = False
                st.rerun()

    # 2. 수정 페이지
    elif st.session_state.edit_mode and st.session_state.view_post:
        post = next((x for x in posts if x["no"] == st.session_state.view_post), None)
        if post:
            st.title("✏️ 게시글 수정")
            with st.container(border=True):
                e_title = st.text_input("제목", value=post["title"])
                e_content = st.text_area("내용", value=post["content"], height=400)
                c1, c2 = st.columns(2)
                if c1.button("✅ 수정 완료", use_container_width=True, type="primary"):
                    post["title"] = e_title
                    post["content"] = e_content
                    save_json("data.json", posts, data_sha)
                    st.session_state.edit_mode = False
                    st.rerun()
                if c2.button("🔙 취소", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()

    # 3. 목록 및 본문 보기
    else:
        st.title(f"📂 {st.session_state.category}")
        
        # 행 추가 버튼
        if st.button("➕ 새 게시글 추가", key="main_add_btn"):
            st.session_state.write_mode = True
            st.session_state.view_post = None
            st.rerun()

        st.divider()

        # 본문 보기
        if st.session_state.view_post:
            post = next((x for x in posts if x["no"] == st.session_state.view_post), None)
            if post:
                with st.container(border=True):
                    v1, v2 = st.columns([8, 2])
                    v1.subheader(post["title"])
                    if v2.button("✏️ 수정하기", use_container_width=True):
                        st.session_state.edit_mode = True
                        st.rerun()
                    st.caption(f"📅 {post['date']} | 👀 조회수 {post.get('views',0)}")
                    st.write(post["content"])
                    if st.button("✖️ 닫기"):
                        st.session_state.view_post = None
                        st.rerun()
                st.divider()

        # 목록 출력
        filtered = [p for p in posts if p.get("category") == st.session_state.category]
        if not filtered:
            st.info("게시글이 없습니다.")
        else:
            # 헤더
            h1, h2, h3 = st.columns([1, 7, 1.5])
            h1.write("**번호**")
            h2.write("**제목**")
            h3.write("**관리**")
            
            for p in filtered:
                col1, col2, col3 = st.columns([1, 7, 1.5])
                col1.write(f"{p['no']}")
                if col2.button(p["title"], key=f"v_{p['no']}_{t_key}", use_container_width=True):
                    st.session_state.view_post = p["no"]
                    p["views"] = p.get("views", 0) + 1
                    save_json("data.json", posts, data_sha)
                    st.rerun()
                if col3.button("🗑️ 삭제", key=f"d_{p['no']}_{t_key}", use_container_width=True):
                    posts = [x for x in posts if x["no"] != p["no"]]
                    save_json("data.json", posts, data_sha)
                    st.rerun()
