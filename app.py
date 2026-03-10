import streamlit as st
import json
from github import Github
from datetime import datetime
import time
from PIL import Image
import streamlit.components.v1 as components

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# 1. GitHub 연결
# -----------------------------
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

# -----------------------------
# 2. 데이터 로드
# -----------------------------
@st.cache_data(ttl=300)
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

def save_json(file, data):
    # 데이터 직렬화 전 특수 객체 여부 체크 및 변환
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"저장 오류: {e}")

# -----------------------------
# 3. 리치 텍스트 에디터 컴포넌트
# -----------------------------
def quill_editor(existing_content=""):
    # Quill 에디터 HTML/JS
    # 이미지를 드래그 앤 드롭하면 Base64로 자동 변환되어 본문에 삽입됩니다.
    editor_html = f"""
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <div id="editor" style="height: 400px; background: white;">{existing_content}</div>
    <script>
        var quill = new Quill('#editor', {{
            modules: {{ toolbar: [
                [{{ header: [1, 2, false] }}],
                ['bold', 'italic', 'underline'],
                ['image', 'code-block'],
                ['clean']
            ]}},
            theme: 'snow'
        }});
        
        // 내용이 바뀔 때마다 Streamlit으로 전송
        quill.on('text-change', function() {{
            var content = quill.root.innerHTML;
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: content
            }}, '*');
        }});
    </script>
    """
    return components.html(editor_html, height=450)

# -----------------------------
# 초기 데이터 로드
# -----------------------------
if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]

if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

# -----------------------------
# 세션 상태
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "board"
if "view_post" not in st.session_state:
    st.session_state.view_post = None
if "write_mode" not in st.session_state:
    st.session_state.write_mode = False
if "category" not in st.session_state:
    st.session_state.category = st.session_state.categories[0]

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    st.title("📚 Fast Board")
    c1, c2 = st.columns(2)
    if c1.button("📋 게시판", use_container_width=True):
        st.session_state.mode = "board"
        st.session_state.view_post = None
        st.session_state.write_mode = False
        st.rerun()
    if c2.button("⚙️ 관리", use_container_width=True):
        st.session_state.mode = "admin"
        st.rerun()

    st.divider()
    st.subheader("📁 카테고리")
    for idx, c in enumerate(st.session_state.categories):
        if st.button(
            c,
            key=f"side_{idx}",
            use_container_width=True,
            type="primary" if st.session_state.category == c else "secondary"
        ):
            st.session_state.category = c
            st.session_state.mode = "board"
            st.session_state.view_post = None
            st.session_state.write_mode = False
            st.rerun()

# -----------------------------
# 관리자 모드
# -----------------------------
if st.session_state.mode == "admin":
    st.title("⚙️ 카테고리 관리")
    with st.container(border=True):
        st.subheader("➕ 추가")
        new_cat = st.text_input("새 카테고리")
        if st.button("추가 실행"):
            if new_cat and new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                save_json("categories.json", st.session_state.categories)
                st.rerun()
    with st.container(border=True):
        st.subheader("🗑️ 삭제")
        del_target = st.selectbox("삭제할 대상", st.session_state.categories)
        if st.button("삭제 실행"):
            if len(st.session_state.categories) > 1:
                st.session_state.categories.remove(del_target)
                save_json("categories.json", st.session_state.categories)
                st.rerun()
            else:
                st.error("최소 1개는 필요합니다.")

# -----------------------------
# 게시판 모드
# -----------------------------
else:
    # -------------------------
    # 글쓰기 페이지
    # -------------------------
    if st.session_state.write_mode:
        st.title("📝 새 게시글 작성")
        
        new_title = st.text_input("제목", key="write_title")
        
        st.markdown("### 본문 작성 (이미지를 복사/붙여넣기 하거나 아이콘을 클릭하세요)")
        # HTML 에디터 호출
        rich_content = quill_editor()

        col1, col2 = st.columns(2)
        if col1.button("💾 저장하기", use_container_width=True, type="primary"):
            if new_title and rich_content:
                new_no = max([p.get("no", 0) for p in st.session_state.posts], default=0) + 1
                
                # 에디터에서 넘어온 값은 특수 객체일 수 있으므로 str() 변환
                final_content = str(rich_content)
                
                st.session_state.posts.insert(0, {
                    "no": new_no,
                    "title": new_title,
                    "content": final_content,
                    "category": st.session_state.category,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                
                save_json("data.json", st.session_state.posts)
                st.success("✅ 등록 완료!")
                st.session_state.write_mode = False
                st.rerun()
            else:
                st.warning("제목과 본문을 모두 입력해주세요.")
        
        if col2.button("❌ 취소", use_container_width=True):
            st.session_state.write_mode = False
            st.rerun()

    # -------------------------
    # 게시글 보기 (수정된 부분)
    # -------------------------
    elif st.session_state.view_post:
        post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)

        if post:
            st.title(post["title"])
            st.caption(f"📅 {post.get('date')} | 📂 {post.get('category')}")
            st.divider()

            # 1. HTML 콘텐츠 가져오기
            content_html = post.get("content", "")

            # 2. 화면에 직접 렌더링 (변수에 담아 출력하지 않고 바로 호출)
            # 이미지 크기가 본문을 벗어나지 않도록 style 태그를 포함합니다.
            components.html(f"""
                <style>
                    img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; }}
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                    pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                </style>
                <div>{content_html}</div>
            """, height=600, scrolling=True)

            st.divider()
            if st.button("🔙 목록으로"):
                st.session_state.view_post = None
                st.rerun()

    # -------------------------
    # 게시글 목록
    # -------------------------
    else:
        st.title(f"📂 {st.session_state.category}")
        if st.button("➕ 새 글 추가"):
            st.session_state.write_mode = True
            st.rerun()

        st.divider()
        filtered = [p for p in st.session_state.posts if p.get("category") == st.session_state.category]

        if not filtered:
            st.info("글이 없습니다.")
        else:
            h1, h2, h3 = st.columns([1, 7, 1.5])
            h1.write("**번호**"); h2.write("**제목**"); h3.write("**관리**")

            for p in filtered:
                col1, col2, col3 = st.columns([1, 7, 1.5])
                col1.write(f"{p['no']}")
                if col2.button(p["title"], key=f"list_{p['no']}", use_container_width=True):
                    st.session_state.view_post = p["no"]
                    st.rerun()
                if col3.button("🗑️", key=f"del_{p['no']}", use_container_width=True):
                    st.session_state.posts = [item for item in st.session_state.posts if item["no"] != p["no"]]
                    save_json("data.json", st.session_state.posts)
                    st.rerun()
