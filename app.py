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

# 3. 강화된 커스텀 에디터 (붙여넣기 즉시 동기화)
def custom_rich_editor():
    editor_id = "quill_editor_unique"
    editor_html = f"""
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <div id="{editor_id}" style="height: 450px; background: white; color: black !important;"></div>
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
        var quill = new Quill('#{editor_id}', {{
            modules: {{ toolbar: [[{{'header': [1, 2, false]}}], ['bold', 'italic', 'image', 'code-block']] }},
            placeholder: '이미지를 복사(Ctrl+V)해서 붙여넣으세요...',
            theme: 'snow'
        }});

        // 중요: 모든 변화(붙여넣기 포함)를 감지하여 부모에게 전송
        function sendToStreamlit() {{
            var content = quill.root.innerHTML;
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: content
            }}, '*');
        }}

        quill.on('text-change', function() {{
            sendToStreamlit();
        }});
        
        // 붙여넣기 직후 강제 동기화
        quill.root.addEventListener('paste', function() {{
            setTimeout(sendToStreamlit, 100);
        }});
    </script>
    <style>
        .ql-editor {{ color: black !important; font-size: 16px; min-height: 450px; }}
    </style>
    """
    return components.html(editor_html, height=500)

# 4. 사이드바 (기존 유지)
with st.sidebar:
    st.title("📚 My Board")
    if st.button("📋 게시판 홈", use_container_width=True):
        st.session_state.view_post = None; st.session_state.write_mode = False; st.rerun()
    st.divider()
    for idx, c in enumerate(st.session_state.categories):
        if st.button(c, key=f"side_{idx}", use_container_width=True, type="primary" if st.session_state.category == c else "secondary"):
            st.session_state.category = c; st.session_state.view_post = None; st.session_state.write_mode = False; st.rerun()

# 5. 메인 로직
if st.session_state.write_mode:
    st.title("📝 새 글 작성")
    new_title = st.text_input("제목", key="w_title")
    
    # 에디터 호출
    content_raw = custom_rich_editor()

    col1, col2 = st.columns(2)
    if col1.button("💾 저장하기", type="primary", use_container_width=True):
        # [핵심] DeltaGenerator 객체가 오지 않도록 문자열 변환 및 검증
        final_content = str(content_raw) if content_raw else ""
        
        # 'None'이나 'DeltaGenerator'가 포함된 잘못된 값 필터링
        if new_title and len(final_content) > 20 and "DeltaGenerator" not in final_content:
            new_post = {
                "no": int(time.time()),
                "title": new_title,
                "content": final_content,
                "category": st.session_state.category,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.posts.insert(0, new_post)
            save_json("data.json", st.session_state.posts)
            st.success("등록되었습니다!"); time.sleep(1)
            st.session_state.write_mode = False; st.rerun()
        else:
            st.warning("내용이 아직 인식되지 않았습니다. 이미지를 넣으셨다면 1~2초 후 다시 눌러주세요.")

    if col2.button("❌ 취소", use_container_width=True):
        st.session_state.write_mode = False; st.rerun()

elif st.session_state.view_post:
    post = next((p for p in st.session_state.posts if p["no"] == st.session_state.view_post), None)
    if post:
        st.title(post["title"])
        st.caption(f"{post['date']} | {post['category']}")
        st.divider()
        # [핵심] 배경 흰색, 글자 검은색 강제 적용
        st.markdown(f"""
            <div style="background: white; padding: 25px; border-radius: 10px; border: 1px solid #ddd; color: black !important;">
                <style>
                    .post-body * {{ color: black !important; }}
                    .post-body img {{ max-width: 100%; height: auto; display: block; margin: 15px 0; }}
                </style>
                <div class="post-body">{post['content']}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔙 목록"): st.session_state.view_post = None; st.rerun()

else:
    st.title(f"📂 {st.session_state.category}")
    if st.button("➕ 새 글 추가"): st.session_state.write_mode = True; st.rerun()
    filtered = [p for p in st.session_state.posts if p.get("category") == st.session_state.category]
    for p in filtered:
        c1, c2, c3 = st.columns([1, 7, 1.5])
        c1.write(f"{p['no']}")
        if c2.button(p["title"], key=f"p_{p['no']}", use_container_width=True):
            st.session_state.view_post = p["no"]; st.rerun()
        if c3.button("🗑️", key=f"d_{p['no']}", use_container_width=True):
            st.session_state.posts = [i for i in st.session_state.posts if i["no"] != p["no"]]
            save_json("data.json", st.session_state.posts); st.rerun()
