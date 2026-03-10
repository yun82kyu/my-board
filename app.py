import streamlit as st
import json
from github import Github
from datetime import datetime
import time

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# 1. GitHub 연결 및 최적화 로드
# -----------------------------
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}"); st.stop()

@st.cache_data(ttl=300)
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except: return [], None

def save_json(file, data):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        st.cache_data.clear()
    except Exception as e: st.error(f"저장 오류: {e}")

# 초기 데이터 세션에 담기 (속도 향상)
if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]
if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

# -----------------------------
# 2. 세션 상태 관리
# -----------------------------
if "mode" not in st.session_state: st.session_state.mode = "board" # board / admin
if "view_post" not in st.session_state: st.session_state.view_post = None # 글 번호 저장
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False
if "category" not in st.session_state: st.session_state.category = st.session_state.categories[0]

t_key = str(int(time.time()))

# -----------------------------
# 3. 사이드바
# -----------------------------
with st.sidebar:
    st.title("📚 Fast Board")
    c1, c2 = st.columns(2)
    if c1.button("📋 게시판", use_container_width=True):
        st.session_state.mode = "board"; st.session_state.view_post = None
        st.session_state.write_mode = False; st.session_state.edit_mode = False; st.rerun()
    if c2.button("⚙️ 관리", use_container_width=True):
        st.session_state.mode = "admin"; st.rerun()
    
    st.divider()
    st.subheader("📁 카테고리")
    for idx, c in enumerate(st.session_state.categories):
        if st.button(c, key=f"side_{idx}", use_container_width=True, 
                     type="primary" if st.session_state.category == c else "secondary"):
            st.session_state.category = c; st.session_state.mode = "board"
            st.session_state.view_post = None; st.session_state.write_mode = False; st.rerun()

# -----------------------------
# 4. 관리자 모드 (기존 로직)
# -----------------------------
if st.session_state.mode == "admin":
    st.title("⚙️ 카테고리 관리")
    # (카테고리 추가/수정/삭제 로직 - 기존과 동일하게 작동)
    with st.container(border=True):
        st.subheader("➕ 추가")
        new_cat = st.text_input("새 카테고리")
        if st.button("추가 실행"):
            if new_cat and new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                save_json("categories.json", st.session_state.categories); st.rerun()

    with st.container(border=True):
        st.subheader("🗑️ 삭제")
        del_target = st.selectbox("삭제할 대상", st.session_state.categories)
        if st.button("삭제 실행"):
            if len(st.session_state.categories) > 1:
                st.session_state.categories.remove(del_target)
                save_json("categories.json", st.session_state.categories); st.rerun()
            else: st.error("최소 1개는 필요합니다.")

# -----------------------------
# 5. 게시판 모드 (상세보기 전체페이지화)
# -----------------------------
else:
    # [A] 글쓰기 페이지 (전체)
    if st.session_state.write_mode:
        st.title("📝 새 게시글 작성")
        w_title = st.text_input("제목")
        w_content = st.text_area("내용", height=500)
        col_w1, col_w2 = st.columns(2)
        if col_w1.button("💾 저장하기", use_container_width=True, type="primary"):
            new_no = max([p.get("no",0) for p in st.session_state.posts], default=0) + 1
            st.session_state.posts.insert(0, {
                "no": new_no, "title": w_title, "content": w_content,
                "category": st.session_state.category, "date": datetime.now().strftime("%Y-%m-%d")
            })
            save_json("data.json", st.session_state.posts)
            st.session_state.write_mode = False; st.rerun()
        if col_w2.button("❌ 취소", use_container_width=True):
            st.session_state.write_mode = False; st.rerun()

    # [B] 본문 보기 페이지 (전체)
    elif st.session_state.view_post:
        post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)
        if post:
            st.title(post["title"])
            st.caption(f"📅 {post.get('date', 'N/A')} | 📂 {post.get('category')}")
            st.divider()
            st.markdown(post["content"]) # 본문을 시원하게 출력
            st.divider()
            
            col_v1, col_v2, col_v3 = st.columns([1, 1, 4])
            if col_v1.button("✏️ 수정", use_container_width=True):
                st.session_state.edit_mode = True; st.rerun()
            if col_v2.button("🔙 목록으로", use_container_width=True):
                st.session_state.view_post = None; st.rerun()
                
            # 수정 모드 진입 시 (본문 보기 중첩)
            if st.session_state.edit_mode:
                st.divider()
                e_title = st.text_input("수정 제목", value=post["title"])
                e_content = st.text_area("수정 내용", value=post["content"], height=400)
                if st.button("✅ 수정 완료"):
                    post["title"], post["content"] = e_title, e_content
                    save_json("data.json", st.session_state.posts)
                    st.session_state.edit_mode = False; st.rerun()

    # [C] 게시글 목록 페이지 (기본)
    else:
        st.title(f"📂 {st.session_state.category}")
        if st.button("➕ 새 글 추가"):
            st.session_state.write_mode = True; st.rerun()
            
        st.divider()
        filtered = [p for p in st.session_state.posts if p.get("category") == st.session_state.category]
        if not filtered:
            st.info("글이 없습니다.")
        else:
            # 목록 헤더
            h1, h2, h3 = st.columns([1, 7, 1.5])
            h1.write("**번호**"); h2.write("**제목**"); h3.write("**관리**")
            
            for p in filtered:
                col1, col2, col3 = st.columns([1, 7, 1.5])
                col1.write(f"{p['no']}")
                # 제목 클릭 시 'view_post'에 번호를 넣고 리런 -> 전체 페이지 본문 보기로 이동
                if col2.button(p["title"], key=f"list_{p['no']}", use_container_width=True):
                    st.session_state.view_post = p["no"]; st.rerun()
                if col3.button("🗑️", key=f"del_{p['no']}", use_container_width=True):
                    st.session_state.posts = [item for item in st.session_state.posts if item['no'] != p['no']]
                    save_json("data.json", st.session_state.posts); st.rerun()
