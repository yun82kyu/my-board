import streamlit as st
import json
from github import Github
from datetime import datetime
import time
import streamlit.components.v1 as components

# -----------------------------
# 1. 기존 설정 및 데이터 로드 (유지)
# -----------------------------
st.set_page_config(page_title="My Board", layout="wide")

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
    curr = st.session_state.repo.get_contents(file)
    st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
    st.cache_data.clear()

# -----------------------------
# 2. 에디터 컴포넌트 (HTML 전송 로직 수정)
# -----------------------------
def quill_editor():
    # 에디터에서 작성된 내용을 Streamlit의 'value'로 전달하는 JS 포함
    editor_html = """
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <div id="editor" style="height: 350px;"></div>
    <script>
        var quill = new Quill('#editor', {
            modules: { toolbar: [[{header: [1,2,false]}], ['bold','italic','image','code-block']] },
            theme: 'snow'
        });
        // 내용이 변할 때마다 부모(Streamlit)에게 데이터 전송
        quill.on('text-change', function() {
            var html = quill.root.innerHTML;
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: html
            }, '*');
        });
    </script>
    """
    # 여기서 리턴되는 값은 에디터의 HTML 내용 문자열입니다.
    return components.html(editor_html, height=420)

# 초기 데이터 로드 (유지)
if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []
if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]
if "category" not in st.session_state:
    st.session_state.category = st.session_state.categories[0]

# --- 사이드바 (유지) ---
with st.sidebar:
    st.title("📚 Fast Board")
    if st.button("📋 게시판", use_container_width=True):
        st.session_state.mode = "board"; st.session_state.view_post = None; st.session_state.write_mode = False; st.rerun()
    # ... (카테고리 선택 로직 동일)

# -----------------------------
# 3. 게시판 로직 (핵심 수정)
# -----------------------------
if st.session_state.get("write_mode"):
    st.title("📝 새 게시글 작성")
    new_title = st.text_input("제목")
    
    # 에디터를 실행하고 결과(HTML 문자열)를 받음
    rich_html = quill_editor()
    
    col1, col2 = st.columns(2)
    if col1.button("💾 저장하기", type="primary"):
        if new_title and rich_html:
            # rich_html은 DeltaGenerator가 아니라 에디터가 보낸 문자열입니다.
            new_post = {
                "no": int(time.time()),
                "title": new_title,
                "content": str(rich_html), # 확실하게 문자열로 변환
                "category": st.session_state.category,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.posts.insert(0, new_post)
            save_json("data.json", st.session_state.posts)
            st.session_state.write_mode = False
            st.rerun()
        else:
            st.warning("내용을 입력 중입니다... (이미지를 넣었다면 잠시만 기다려주세요)")

elif st.session_state.get("view_post"):
    post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)
    if post:
        st.title(post["title"])
        st.caption(f"📅 {post['date']} | 📂 {post['category']}")
        st.divider()

        # [수정 포인트] st.write(post['content']) 가 아니라 components.html()을 사용
        components.html(f"""
            <style>
                img {{ max-width: 100%; height: auto; display: block; margin: 10px 0; }}
                body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
            </style>
            <div>{post['content']}</div>
        """, height=800, scrolling=True)

        if st.button("🔙 목록으로"):
            st.session_state.view_post = None; st.rerun()

else:
    # --- 목록 출력 (유지) ---
    st.title(f"📂 {st.session_state.category}")
    if st.button("➕ 새 글 추가"):
        st.session_state.write_mode = True; st.rerun()
    # ... (목록 테이블 로직 동일)
