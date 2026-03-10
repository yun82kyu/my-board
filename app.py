import streamlit as st
import json
from github import Github
from datetime import datetime
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# 1. GitHub 연결 및 설정
# -----------------------------
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

# -----------------------------
# 2. 데이터 로드/저장 함수
# -----------------------------
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None

def save_json(file, data):
    try:
        json_string = json.dumps(data, indent=4, ensure_ascii=False)
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        st.session_state.posts = data # 세션 데이터 즉시 갱신
    except Exception as e:
        st.error(f"저장 오류: {e}")

# 초기 데이터 로드
if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]

# 세션 상태 초기화
if "mode" not in st.session_state: st.session_state.mode = "board"
if "view_post" not in st.session_state: st.session_state.view_post = None
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "category" not in st.session_state: 
    st.session_state.category = st.session_state.categories[0]

# -----------------------------
# 3. 커스텀 에디터 (드래그앤드롭 & 복사붙여넣기 강화)
# -----------------------------
def custom_rich_editor():
    # Quill 에디터: 이미지 처리 능력이 가장 뛰어난 설정
    editor_html = """
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <style>
        #editor-container { height: 450px; background: white; color: black !important; font-size: 16px; }
        .ql-editor { color: black !important; }
        .ql-editor.ql-blank::before { color: rgba(0,0,0,0.3) !important; }
    </style>
    <div id="editor-container"></div>
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
        var quill = new Quill('#editor-container', {
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    ['blockquote', 'code-block'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['link', 'image'],
                    ['clean']
                ]
            },
            placeholder: '여기에 내용을 작성하거나 이미지를 드래그해서 넣으세요...',
            theme: 'snow'
        });

        // 사용자가 입력할 때마다 Streamlit으로 HTML 데이터 전송
        quill.on('text-change', function() {
            var content = quill.root.innerHTML;
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: content
            }, '*');
        });
    </script>
    """
    return components.html(editor_html, height=500)

# -----------------------------
# 4. 사이드바 메뉴
# -----------------------------
with st.sidebar:
    st.title("📚 Fast Board")
    if st.button("📋 전체 게시판", use_container_width=True):
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
# 5. 메인 게시판 로직
# -----------------------------

# [글쓰기 화면]
if st.session_state.write_mode:
    st.title("📝 새 게시글 작성")
    new_title = st.text_input("제목", key="write_title", placeholder="제목을 입력하세요")
    
    st.markdown("#### 본문 내용")
    st.info("💡 **팁:** 이미지는 드래그해서 넣거나, 캡처 후 `Ctrl+V`로 바로 붙여넣을 수 있습니다.")
    
    # 에디터 호출 및 데이터 수신
    rich_content = custom_rich_editor()

    col1, col2 = st.columns(2)
    if col1.button("💾 저장하기", use_container_width=True, type="primary"):
        # 데이터가 DeltaGenerator 객체인지 문자열인지 판별하여 처리
        final_body = str(rich_content) if rich_content else ""
        
        if new_title and final_body and "DeltaGenerator" not in final_body:
            new_no = max([p.get("no", 0) for p in st.session_state.posts], default=0) + 1
            new_post = {
                "no": new_no,
                "title": new_title,
                "content": final_body,
                "category": st.session_state.category,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.posts.insert(0, new_post)
            save_json("data.json", st.session_state.posts)
            st.success("✅ 게시글이 등록되었습니다!")
            time.sleep(1)
            st.session_state.write_mode = False
            st.rerun()
        else:
            st.warning("제목과 본문을 확인해주세요. (본문을 막 작성했다면 1초 뒤에 눌러주세요)")
            
    if col2.button("❌ 취소", use_container_width=True):
        st.session_state.write_mode = False
        st.rerun()

# [상세 보기 화면]
elif st.session_state.view_post:
    post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)

    if post:
        st.title(post["title"])
        st.caption(f"📅 {post.get('date')} | 📂 {post.get('category')}")
        st.divider()

        # 글자색 검정 고정 및 이미지 자동 크기 조절 스타일 적용
        st.markdown(f"""
            <div style="background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #eee; color: #333 !important;">
                <style>
                    .rendered-html * {{ color: #333 !important; font-size: 16px; line-height: 1.7; }}
                    .rendered-html img {{ max-width: 100%; height: auto; display: block; margin: 20px 0; border-radius: 10px; }}
                    .rendered-html pre {{ background: #f4f4f4; padding: 15px; border-radius: 8px; color: #d63384 !important; }}
                </style>
                <div class="rendered-html">
                    {post.get('content', '')}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        if st.button("🔙 목록으로 돌아가기"):
            st.session_state.view_post = None
            st.rerun()

# [목록 화면]
else:
    st.title(f"📂 {st.session_state.category}")
    if st.button("➕ 새 글 추가하기", type="primary"):
        st.session_state.write_mode = True
        st.rerun()
    
    st.divider()
    filtered = [p for p in st.session_state.posts if p.get("category") == st.session_state.category]
    
    if not filtered:
        st.info("이 카테고리에 등록된 글이 없습니다.")
    else:
        # 헤더
        h1, h2, h3 = st.columns([1, 7, 1.5])
        h1.write("**번호**"); h2.write("**제목**"); h3.write("**관리**")
        
        for p in filtered:
            c1, c2, c3 = st.columns([1, 7, 1.5])
            c1.write(f"{p['no']}")
            if c2.button(p["title"], key=f"post_{p['no']}", use_container_width=True):
                st.session_state.view_post = p["no"]
                st.rerun()
            if c3.button("🗑️", key=f"del_{p['no']}", use_container_width=True):
                st.session_state.posts = [item for item in st.session_state.posts if item["no"] != p["no"]]
                save_json("data.json", st.session_state.posts)
                st.rerun()
