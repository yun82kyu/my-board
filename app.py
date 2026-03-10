import streamlit as st
import json
from github import Github

# --- 1. 보안 설정 및 데이터 로드 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

@st.cache_data(show_spinner=False)
def load_json(file_name):
    content = repo.get_contents(file_name)
    return json.loads(content.decoded_content.decode("utf-8")), content.sha

def save_json(file_name, data, sha):
    repo.update_file(file_name, "Update", json.dumps(data, indent=4, ensure_ascii=False), sha)
    st.cache_data.clear()

# --- 2. 기본 설정 ---
st.set_page_config(page_title="Admin Panel", layout="wide")

params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

categories, cat_sha = load_json("categories.json")
data, data_sha = load_json("data.json") # 삭제 확인을 위해 데이터를 미리 로드

if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0]

# --- 3. 좌측 사이드바 (추가 및 안전한 삭제) ---
with st.sidebar:
    col_h1, col_h2 = st.columns([3, 1])
    col_h1.subheader("📁 대분류")
    with col_h2:
        with st.popover("➕"):
            new_name = st.text_input("분류명 입력")
            if st.button("추가", use_container_width=True):
                if new_name and new_name not in categories:
                    categories.append(new_name)
                    save_json("categories.json", categories, cat_sha)
                    st.rerun()

    st.divider()
    
    for idx, cat in enumerate(categories):
        side_c1, side_c2 = st.columns([4, 1])
        
        # 1. 카테고리 선택 버튼
        is_sel = (st.session_state.current_cat == cat)
        if side_c1.button(cat, key=f"s_{cat}", use_container_width=True, type="primary" if is_sel else "secondary"):
            st.session_state.current_cat = cat
            st.query_params.clear()
            st.rerun()
            
        # 2. 안전한 삭제 버튼 (Popover 활용)
        with side_c2.popover("🗑️"):
            # 해당 카테고리에 글이 있는지 확인
            post_count = len([i for i in data if i.get('category') == cat])
            
            if post_count > 0:
                st.warning(f"'{cat}'에 {post_count}개의 글이 있습니다.")
                st.write("분류를 삭제하면 글을 관리하기 어려워질 수 있습니다. 정말 삭제할까요?")
            else:
                st.write("이 분류를 삭제하시겠습니까?")
            
            if st.button("✅ 네, 삭제합니다", key=f"confirm_del_{idx}", use_container_width=True, type="danger"):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("최소 1개는 남겨야 합니다.")

# --- 4. 메인 화면 - 상세 페이지 ---
if current_view == "detail" and selected_no:
    post = next((i for i in data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록으로"): st.query_params.clear(); st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    st.stop()

# --- 5. 메인 화면 - 목록 ---
st.title(f"👤 {st.session_state.current_cat}")

filtered_data = [i for i in data if i.get('category') == st.session_state.current_cat]

search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", label_visibility="collapsed")

with write_c.popover("📝 신규 행 추가", use_container_width=True):
    with st.form("new_post"):
        new_t = st.text_input("제목")
        new_c = st.text_area("내용")
        if st.form_submit_button("저장"):
            new_no = max([int(i['no']) for i in data]) + 1 if data else 1
            data.insert(0, {"no": new_no, "title": new_t, "name": "관리자", "content": new_c, "viewcnt": 0, "category": st
