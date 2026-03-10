import streamlit as st
import json
from github import Github
from datetime import datetime
import time # 키 충돌 방지용

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
# 데이터 로드 (캐시 적용으로 속도 향상)
# -----------------------------
@st.cache_data(show_spinner=False)
def load_json(file):
    try:
        content = repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

# -----------------------------
# 데이터 저장
# -----------------------------
def save_json(file, data, sha=None):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        if sha is None: # 파일이 없는 경우 새로 생성
            try:
                curr_content = repo.get_contents(file)
                sha = curr_content.sha
            except:
                pass
        
        if sha:
            repo.update_file(file, f"update {file}", json_string, sha)
        else:
            repo.create_file(file, f"create {file}", json_string)
        
        st.cache_data.clear() # 저장 후 캐시 초기화하여 최신 데이터 반영
    except Exception as e:
        st.error(f"저장 실패: {e}")

# 데이터 로드
categories, cat_sha = load_json("categories.json")
posts, data_sha = load_json("data.json")

if not categories:
    categories = ["기본분류"]
    save_json("categories.json", categories)

# -----------------------------
# 세션 상태 및 고유 키 생성
# -----------------------------
if "mode" not in st.session_state: st.session_state.mode = "board"
if "category" not in st.session_state: st.session_state.category = categories[0]
if "view_post" not in st.session_state: st.session_state.view_post = None

# 🌟 중요: 버튼 충돌 방지를 위한 유니크 런타임 ID
t_key = str(int(time.time()))

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    st.title("📚 내 미니 보드")
    
    col1, col2 = st.columns(2)
    if col1.button("📋 게시판", key="nav_board", use_container_width=True):
        st.session_state.mode = "board"
        st.session_state.view_post = None
        st.rerun()
    if col2.button("⚙️ 관리", key="nav_admin", use_container_width=True):
        st.session_state.mode = "admin"
        st.rerun()

    st.divider()

    # 🌟 조건문(if st.session_state.mode == "board":)을 제거했습니다.
    # 이제 '관리' 모드에서도 카테고리 리스트가 보입니다.
    st.subheader("📁 카테고리 목록")
    for idx, c in enumerate(categories):
        is_active = (st.session_state.category == c)
        if st.button(c, key=f"side_cat_{idx}_{t_key}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.category = c
            st.session_state.view_post = None
            # 카테고리를 클릭하면 자동으로 '게시판' 모드로 전환되게 하고 싶다면 아래줄 추가
            st.session_state.mode = "board" 
            st.rerun()

# -----------------------------
# 관리자 모드
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
                # 게시글 카테고리 일괄 변경
                for p in posts:
                    if p.get("category") == edit_target: p["category"] = new_name
                save_json("categories.json", categories, cat_sha)
                save_json("data.json", posts, data_sha)
                st.rerun()

    with st.container(border=True):
        st.subheader("🗑️ 삭제")
        del_target = st.selectbox("삭제할 대상", categories, key="admin_del_sel")
        if st.button("카테고리 삭제 실행", key="admin_del_btn"):  # type="danger" 삭제
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
# 게시판 모드
# -----------------------------
else:
    st.title(f"📂 {st.session_state.category}")

    # 글쓰기
    with st.expander("✏️ 글쓰기", expanded=False):
        with st.form("write_form", clear_on_submit=True):
            title = st.text_input("제목")
            content = st.text_area("내용")
            if st.form_submit_button("등록"):
                if title and content:
                    new_no = max([p.get("no",0) for p in posts], default=0) + 1
                    posts.insert(0, {
                        "no": new_no,
                        "title": title,
                        "content": content,
                        "category": st.session_state.category,
                        "views": 0,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_json("data.json", posts, data_sha)
                    st.rerun()

    st.divider()

    # 게시글 리스트
    filtered = [p for p in posts if p.get("category") == st.session_state.category]

    if not filtered:
        st.info("이 카테고리에 게시글이 없습니다.")
    else:
        for p in filtered:
            col1, col2, col3 = st.columns([1, 7, 1.5])
            col1.write(f"#{p['no']}")
            # 상세 보기 버튼 (유니크 키 적용)
            if col2.button(p["title"], key=f"view_{p['no']}_{t_key}", use_container_width=True):
                st.session_state.view_post = p["no"]
                p["views"] = p.get("views", 0) + 1
                save_json("data.json", posts, data_sha)
                st.rerun()
            
            if col3.button("🗑️ 삭제", key=f"del_{p['no']}_{t_key}", use_container_width=True):
                posts = [x for x in posts if x["no"] != p["no"]]
                save_json("data.json", posts, data_sha)
                st.rerun()

    # 게시글 본문 출력
    if st.session_state.view_post:
        post = next((x for x in posts if x["no"] == st.session_state.view_post), None)
        if post:
            st.markdown("---")
            st.subheader(post["title"])
            st.caption(f"📅 {post['date']} | 👀 조회수 {post.get('views',0)}")
            st.info(post["content"])
            if st.button("닫기", key="close_post"):
                st.session_state.view_post = None
                st.rerun()
