import streamlit as st
import json
from github import Github
from datetime import datetime
import time

st.set_page_config(page_title="My Board", layout="wide")

# --- 1. GitHub 연결 (전역 객체로 한 번만 생성) ---
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

# --- 2. 데이터 로드/저장 (속도 최적화) ---
# ttl을 600초(10분)로 설정하여 잦은 통신 방지
@st.cache_data(ttl=600, show_spinner="데이터를 가져오는 중...")
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

def save_json(file, data):
    """저장할 때만 GitHub 통신 발생"""
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        # 최신 SHA 값을 가져와서 충돌 방지
        curr_content = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr_content.sha)
        st.cache_data.clear() # 저장 후 캐시 초기화
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")

# 초기 데이터 로드
if "categories" not in st.session_state or "posts" not in st.session_state:
    cats, _ = load_json("categories.json")
    pts, _ = load_json("data.json")
    st.session_state.categories = cats if cats else ["기본분류"]
    st.session_state.posts = pts if pts else []

# --- 3. 세션 상태 관리 ---
if "mode" not in st.session_state: st.session_state.mode = "board"
if "category" not in st.session_state: st.session_state.category = st.session_state.categories[0]
if "view_post" not in st.session_state: st.session_state.view_post = None
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

# --- 4. 메인 로직 (메모리 우선 처리) ---

# [사이드바]
with st.sidebar:
    st.title("🚀 Fast Board")
    c1, c2 = st.columns(2)
    if c1.button("📋 게시판", use_container_width=True):
        st.session_state.mode = "board"; st.session_state.view_post = None; st.rerun()
    if c2.button("⚙️ 관리", use_container_width=True):
        st.session_state.mode = "admin"; st.rerun()
    
    st.divider()
    for c in st.session_state.categories:
        if st.button(c, use_container_width=True, type="primary" if st.session_state.category == c else "secondary"):
            st.session_state.category = c; st.session_state.mode = "board"; st.session_state.view_post = None; st.rerun()

# [관리자 모드]
if st.session_state.mode == "admin":
    st.title("⚙️ 관리")
    # 카테고리 추가/삭제 시 st.session_state.categories를 직접 수정 후 save_json 호출
    # (기존 로직과 동일하되 세션 스테이트를 먼저 수정하면 훨씬 빠름)
    new_cat = st.text_input("새 카테고리")
    if st.button("추가"):
        if new_cat and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            save_json("categories.json", st.session_state.categories)
            st.rerun()

# [게시판 모드]
else:
    # 글쓰기 모드
    if st.session_state.write_mode:
        t = st.text_input("제목")
        c = st.text_area("내용", height=300)
        if st.button("저장"):
            new_post = {"no": int(time.time()), "title": t, "content": c, "category": st.session_state.category, "date": datetime.now().strftime("%Y-%m-%d")}
            st.session_state.posts.insert(0, new_post)
            save_json("data.json", st.session_state.posts)
            st.session_state.write_mode = False; st.rerun()
    
    # 목록 보기
    else:
        if st.button("➕ 행 추가"):
            st.session_state.write_mode = True; st.rerun()
            
        filtered = [p for p in st.session_state.posts if p.get("category") == st.session_state.category]
        for p in filtered:
            col1, col2, col3 = st.columns([1, 7, 1])
            col1.write(p['no'])
            # 🌟 속도 개선 핵심: 제목 클릭 시 저장(조회수)을 하지 않고 메모리에서만 처리하거나 그냥 보여주기
            if col2.button(p['title'], key=f"btn_{p['no']}", use_container_width=True):
                st.session_state.view_post = p['no']; st.rerun()
            if col3.button("🗑️", key=f"del_{p['no']}"):
                st.session_state.posts = [item for item in st.session_state.posts if item['no'] != p['no']]
                save_json("data.json", st.session_state.posts)
                st.rerun()
        
        if st.session_state.view_post:
            post = next((x for x in st.session_state.posts if x['no'] == st.session_state.view_post), None)
            if post:
                st.info(f"### {post['title']}\n\n{post['content']}")
