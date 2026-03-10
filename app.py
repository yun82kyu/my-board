import streamlit as st
import json
import os
from github import Github
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="My Rich Board", layout="wide")

# 1. GitHub 연결 (기존 로직 유지)
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
except Exception as e:
    st.error("GitHub 연결 실패. secrets 설정을 확인하세요.")
    st.stop()

# 2. 데이터 로드/저장 함수
def load_json(file):
    try:
        content = repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except: return [], None

def save_json(file, data):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    curr = repo.get_contents(file)
    repo.update_file(file, "update data", json_string, curr.sha)

# 3. Summernote 에디터 컴포넌트 (HTML/JS)
def summernote_editor():
    # 에디터의 HTML 소스
    editor_html = """
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/summernote/0.8.18/summernote.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/summernote/0.8.18/summernote.js"></script>
    
    <div id="summernote"></div>
    <button id="saveBtn" class="btn btn-primary btn-block" style="margin-top:10px;">본문 확정하기</button>

    <script>
        $(document).ready(function() {
            $('#summernote').summernote({
                height: 400,
                placeholder: '내용을 입력하고 이미지를 드래그해서 넣으세요.',
                callbacks: {
                    onChange: function(contents) {
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: contents}, '*');
                    }
                }
            });
            $('#saveBtn').click(function() {
                const content = $('#summernote').summernote('code');
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: content}, '*');
                alert("본문이 준비되었습니다. 아래 저장 버튼을 눌러주세요.");
            });
        });
    </script>
    """
    # Streamlit에 HTML 에디터 표시
    return components.html(editor_html, height=520)

# --- 메인 화면 로직 ---
if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts

if "write_mode" not in st.session_state:
    st.session_state.write_mode = False

# 글쓰기 모드
if st.session_state.write_mode:
    st.title("📝 새 글 작성 (에디터)")
    title = st.text_input("제목")
    category = st.selectbox("카테고리", ["OOP", "LLM", "Python"])
    
    st.info("💡 아래 에디터에서 작성 후 '본문 확정하기'를 먼저 눌러주세요.")
    # 에디터 호출 및 결과값 받기
    content_data = summernote_editor()
    
    # 실제 저장 버튼
    if st.button("🚀 최종 저장 및 업로드"):
        if title and content_data:
            new_no = max([p.get("no", 0) for p in st.session_state.posts], default=0) + 1
            new_post = {
                "no": new_no,
                "title": title,
                "category": category,
                "content": content_data, # HTML (이미지 포함)
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.posts.insert(0, new_post)
            save_json("data.json", st.session_state.posts)
            st.session_state.write_mode = False
            st.rerun()
        else:
            st.warning("제목과 본문을 확인해주세요.")
            
    if st.button("취소"):
        st.session_state.write_mode = False
        st.rerun()

# 게시글 목록/보기 모드
else:
    st.title("📚 My Rich Board")
    if st.button("➕ 새 글 작성"):
        st.session_state.write_mode = True
        st.rerun()

    for post in st.session_state.posts:
        with st.expander(f"[{post.get('category')}] {post.get('title')} ({post.get('date')})"):
            # HTML 렌더링 (이미지 포함)
            st.components.v1.html(post.get('content'), height=500, scrolling=True)
            if st.button("삭제", key=f"del_{post['no']}"):
                st.session_state.posts = [p for p in st.session_state.posts if p['no'] != post['no']]
                save_json("data.json", st.session_state.posts)
                st.rerun()
