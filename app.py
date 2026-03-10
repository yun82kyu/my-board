import streamlit as st
import json
from github import Github
from datetime import datetime
import time
from streamlit_quill import st_quill

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# 1. GitHub 연결 (기존 유지)
# -----------------------------
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

# -----------------------------
# 2. 데이터 로드/저장 (캐시 초기화 보강)
# -----------------------------
def load_json(file):
    try:
        # 캐시를 쓰지 않고 직접 가져와서 데이터 동기화 오류 방지
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

def save_json(file, data):
    try:
        json_string = json.dumps(data, indent=4, ensure_ascii=False)
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        # 데이터 갱신 후 세션 상태의 posts도 최신화
        st.session_state.posts = data 
    except Exception as e:
        st.error(f"저장 오류: {e}")

# 초기 데이터 로드 (최초 1회만)
if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]

# 세션 상태 관리
if "mode" not in st.session_state: st.session_state.mode = "board"
if "view_post" not in st.session_state: st.session_state.view_post = None
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "category" not in st.session_state: 
    st.session_state.category = st.session_state.categories[0]

# --- 사이드바 ---
with st.sidebar:
    st.title("📚 Fast Board")
    if st.button("📋 게시판", use_container_width=True):
        st.session_state.view_post = None
        st.session_state.write_mode = False
        st.rerun()
    
    st.divider()
    st.subheader("📁 카테고리")
    for idx, c in enumerate(st.session_state.categories):
        if st.button(c, key=f"side_{idx}", use_container_width=True, 
                     type="primary" if st.session_state.category == c else "secondary"):
            st.session_state.category = c
            st.session_state.view_post = None
            st.session_state.write_mode = False
            st.rerun()

# -----------------------------
# 3. 메인 로직
# -----------------------------

# [A] 글쓰기 모드
if st.session_state.write_mode:
    st.title("📝 새 게시글 작성")
    new_title = st.text_input("제목", key="write_title")
    
    st.subheader("본문 내용")
    # Quill 에디터 실행
    content_data = st_quill(
        placeholder="이미지는 Ctrl+V로 붙여넣으세요.",
        key="quill_editor",
        html=True
    )

    col1, col2 = st.columns(2)
    if col1.button("💾 저장하기", use_container_width=True, type="primary"):
        # content_data가 DeltaGenerator가 아닌 실제 내용(문자열)인지 확인
        actual_content = str(content_data) if content_data else ""
        
        if new_title and actual_content and "DeltaGenerator" not in actual_content:
            new_no = max([p.get("no", 0) for p in st.session_state.posts], default=0) + 1
            new_post = {
                "no": new_no,
                "title": new_title,
                "content": actual_content,
                "category": st.session_state.category,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.posts.insert(0, new_post)
            save_json("data.json", st.session_state.posts)
            st.success("✅ 등록 완료!")
            st.session_state.write_mode = False
            time.sleep(1) # 저장이 GitHub에 반영될 시간 확보
            st.rerun()
        else:
            st.warning("내용을 입력해주세요. (입력 직후라면 에디터 밖을 한 번 클릭 후 저장하세요)")
            
    if col2.button("❌ 취소", use_container_width=True):
        st.session_state.write_mode = False
        st.rerun()

# [B] 상세보기 모드
elif st.session_state.view_post:
    post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)

    if post:
        st.title(post["title"])
        st.caption(f"📅 {post.get('date')} | 📂 {post.get('category')}")
        st.divider()

        # DeltaGenerator 에러를 방지하기 위해 순수 HTML만 추출하여 렌더링
        raw_html = str(post.get("content", ""))
        
        # 만약 저장된 데이터에 DeltaGenerator 문구가 포함되어 있다면 제거 시도
        if "DeltaGenerator" in raw_html:
            st.error("데이터 저장 오류가 감지되었습니다. 다시 작성해주세요.")
        else:
            st.markdown(f"""
                <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee;">
                    <style>
                        img {{ max-width: 100%; height: auto; display: block; margin: 15px 0; border-radius: 8px; }}
                    </style>
                    {raw_html}
                </div>
            """, unsafe_allow_html=True)

        st.divider()
        if st.button("🔙 목록으로"):
            st.session_state.view_post = None
            st.rerun()

# [C] 목록 모드
else:
    st.title(f"📂 {st.session_state.category}")
    if st.button("➕ 새 글 추가"):
        st.session_state.write_mode = True
        st.rerun()
    
    st.divider()
    filtered = [p for p in st.session_state.posts if p.get("category") == st.session_state.category]
    
    if not filtered:
        st.info("작성된 글이 없습니다.")
    else:
        for p in filtered:
            c1, c2, c3 = st.columns([1, 7, 1.5])
            c1.write(f"{p['no']}")
            if c2.button(p["title"], key=f"btn_{p['no']}", use_container_width=True):
                st.session_state.view_post = p["no"]
                st.rerun()
            if c3.button("🗑️", key=f"del_{p['no']}", use_container_width=True):
                st.session_state.posts = [item for item in st.session_state.posts if item["no"] != p["no"]]
                save_json("data.json", st.session_state.posts)
                st.rerun()
