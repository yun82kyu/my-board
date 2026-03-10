import streamlit as st
import json
from github import Github
from datetime import datetime
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="My Board", layout="wide")

# 1. GitHub 연결 (기존 유지)
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}"); st.stop()

# 2. 데이터 로드/저장 (기존 유지)
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except: return [], None

def save_json(file, data):
    try:
        json_string = json.dumps(data, indent=4, ensure_ascii=False)
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        st.session_state.posts = data
    except Exception as e: st.error(f"저장 오류: {e}")

if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]

if "view_post" not in st.session_state: st.session_state.view_post = None
if "write_mode" not in st.session_state: st.session_state.write_mode = False
if "category" not in st.session_state: st.session_state.category = st.session_state.categories[0]

# 3. 드래그앤드랍 보강 커스텀 에디터
def custom_rich_editor():
    editor_html = """
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <style>
        #editor-container { height: 450px; background: white; color: black !important; }
        .ql-editor { color: black !important; font-size: 16px; }
    </style>
    <div id="editor-container"></div>
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
        var quill = new Quill('#editor-container', {
            modules: {
                toolbar: [
                    [{'header': [1, 2, false]}],
                    ['bold', 'italic', 'image', 'code-block'],
                    ['clean']
                ]
            },
            placeholder: '여기에 내용을 쓰거나 이미지를 드래그해서 넣으세요...',
            theme: 'snow'
        });

        // 데이터 전송 함수
        function sendToStreamlit() {
            var content = quill.root.innerHTML;
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: content
            }, '*');
        }

        // 텍스트 변경 시 즉시 전송
        quill.on('text-change', function() {
            sendToStreamlit();
        });

        // 드롭(Drop) 또는 붙여넣기(Paste) 이벤트 발생 시 약간의 지연 후 강제 전송
        ['drop', 'paste'].forEach(evt => {
            quill.root.addEventListener(evt, function() {
                setTimeout(sendToStreamlit, 500); // 이미지 처리 시간 확보
            }, false);
        });
    </script>
    """
    return components.html(editor_html, height=500)

# 4. 메인 로직
if st.session_state.write_mode:
    st.title("📝 새 글 작성")
    new_title = st.text_input("제목", key="w_title")
    
    # 에디터 호출
    content_raw = custom_rich_editor()

    # 데이터 수신 상태 확인 (디버깅용 겸 안전장치)
    content_str = str(content_raw) if content_raw else ""
    is_ready = len(content_str) > 20 and "DeltaGenerator" not in content_str

    if is_ready:
        st.success("✅ 본문 데이터 연결됨 (저장 가능)")
    else:
        st.warning("⚠️ 본문을 작성 중이거나 이미지를 처리 중입니다...")

    col1, col2 = st.columns(2)
    if col1.button("💾 저장하기", type="primary", use_container_width=True, disabled=not is_ready):
        new_post = {
            "no": int(time.time()),
            "title": new_title,
            "content": content_str,
            "category": st.session_state.category,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state.posts.insert(0, new_post)
        save_json("data.json", st.session_state.posts)
        st.success("등록되었습니다!"); time.sleep(1)
        st.session_state.write_mode = False; st.rerun()

    if col2.button("❌ 취소", use_container_width=True):
        st.session_state.write_mode = False; st.rerun()

elif st.session_state.view_post:
    # --- 상세보기 로직 ---
    post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)
    if post:
        st.title(post["title"])
        st.caption(f"{post['date']} | {post['category']}")
        st.divider()
        st.markdown(f"""
            <div style="background: white; padding: 25px; border-radius: 10px; border: 1px solid #ddd; color: black !important;">
                <style> .post-body * {{ color: black !important; }} .post-body img {{ max-width: 100%; height: auto; display: block; margin: 15px 0; }} </style>
                <div class="post-body">{post['content']}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔙 목록"): st.session_state.view_post = None; st.rerun()

else:
    # --- 목록 로직 (기존 유지) ---
    st.title(f"📂 {st.session_state.category}")
    if st.button("➕ 새 글 추가"): st.session_state.write_mode = True; st.rerun()
    # (카테고리별 필터링 및 버튼 출력 로직)
    for p in [p for p in st.session_state.posts if p.get("category") == st.session_state.category]:
        c1, c2, c3 = st.columns([1, 7, 1.5])
        c1.write(f"{p['no']}")
        if c2.button(p["title"], key=f"p_{p['no']}", use_container_width=True):
            st.session_state.view_post = p["no"]; st.rerun()
        if c3.button("🗑️", key=f"d_{p['no']}", use_container_width=True):
            st.session_state.posts = [i for i in st.session_state.posts if i["no"] != p["no"]]
            save_json("data.json", st.session_state.posts); st.rerun()
