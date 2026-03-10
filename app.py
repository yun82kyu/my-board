import streamlit as st
import json
from github import Github
from datetime import datetime
import time
from streamlit_quill import st_quill  # << 새롭게 추가된 라이브러리

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# 1. GitHub 연결 (기존 로직 유지)
# -----------------------------
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

# -----------------------------
# 2. 데이터 로드/저장 (기존 로직 유지)
# -----------------------------
@st.cache_data(ttl=300)
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

def save_json(file, data):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"저장 오류: {e}")

# 초기 데이터 로드
if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]

if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

# 세션 상태 관리
if "mode" not in st.session_state: st.session_state.mode = "board"
if "view_post" not in st.session_state: st.session_state.view_post = None
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "category" not in st.session_state: st.session_state.category = st.session_state.categories[0]

# --- 사이드바 (기존 유지) ---
with st.sidebar:
    st.title("📚 Fast Board")
    if st.button("📋 게시판", use_container_width=True):
        st.session_state.mode = "board"; st.session_state.view_post = None; st.session_state.write_mode = False; st.rerun()
    # ... (기타 카테고리 버튼 로직 동일)

# -----------------------------
# 3. 게시판 모드 (상세 입력 해결 버전)
# -----------------------------
if st.session_state.write_mode:
    st.title("📝 새 게시글 작성")
    
    new_title = st.text_input("제목", key="write_title")
    
    st.subheader("본문 내용")
    st.info("💡 이미지는 복사(Ctrl+V)해서 붙여넣으세요. 글 중간에 삽입됩니다.")
    
    # [해결책] streamlit-quill 사용
    # 이 함수는 사용자가 입력한 HTML 내용을 즉시 'content' 변수에 담아줍니다.
    content = st_quill(
        placeholder="강의 내용을 작성하세요...",
        key="quill_editor",
        html=True  # HTML 형식으로 저장되도록 설정
    )

    col1, col2 = st.columns(2)
    if col1.button("💾 저장하기", use_container_width=True, type="primary"):
        if new_title and content and content != "<p><br></p>":
            new_no = max([p.get("no", 0) for p in st.session_state.posts], default=0) + 1
            
            st.session_state.posts.insert(0, {
                "no": new_no,
                "title": new_title,
                "content": content,  # 이미지와 텍스트가 섞인 HTML
                "category": st.session_state.category,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            
            save_json("data.json", st.session_state.posts)
            st.success("✅ 등록 완료!")
            st.session_state.write_mode = False
            st.rerun()
        else:
            st.warning("제목과 본문을 입력해주세요.")
            
    if col2.button("❌ 취소", use_container_width=True):
        st.session_state.write_mode = False
        st.rerun()

elif st.session_state.view_post:
    # 1. 선택한 게시글 찾기
    post = next(
        (p for p in st.session_state.posts if p["no"] == st.session_state.view_post),
        None
    )

    if post:
        st.title(post["title"])
        st.caption(f"📅 {post.get('date')} | 📂 {post.get('category')}")
        st.divider()

        # [수정 핵심] 변수에 담긴 HTML 내용을 직접 출력합니다.
        # st_quill을 여기서 다시 호출하면 안 됩니다! 
        # 이미 저장된 post["content"] 문자열을 HTML로 렌더링합니다.
        
        content_html = post.get("content", "")
        
        # 이미지 크기 자동 조절 및 스타일 적용
        display_html = f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: white;">
            <style>
                img {{ max-width: 100%; height: auto; display: block; margin: 10px 0; border-radius: 5px; }}
                p {{ font-size: 16px; line-height: 1.6; }}
            </style>
            {content_html}
        </div>
        """
        
        # 2. DeltaGenerator 에러를 방지하기 위해 markdown의 unsafe_allow_html 사용
        st.markdown(display_html, unsafe_allow_html=True)

        st.divider()
        if st.button("🔙 목록으로"):
            st.session_state.view_post = None
            st.rerun()

else:
    # --- 게시글 목록 (기존 유지) ---
    st.title(f"📂 {st.session_state.category}")
    if st.button("➕ 새 글 추가"):
        st.session_state.write_mode = True; st.rerun()
    
    # (목록 출력 테이블 로직 동일...)
    for p in [p for p in st.session_state.posts if p.get("category") == st.session_state.category]:
        c1, c2, c3 = st.columns([1, 7, 1.5])
        c1.write(f"{p['no']}")
        if c2.button(p["title"], key=f"list_{p['no']}", use_container_width=True):
            st.session_state.view_post = p["no"]; st.rerun()
        if c3.button("🗑️", key=f"del_{p['no']}", use_container_width=True):
            st.session_state.posts = [item for item in st.session_state.posts if item["no"] != p["no"]]
            save_json("data.json", st.session_state.posts); st.rerun()
