import streamlit as st
import json
from github import Github

# --- 1. 보안 설정 및 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- 2. 데이터 처리 함수들 ---
@st.cache_data(show_spinner=False)
def load_github_json(file_name):
    file_content = repo.get_contents(file_name)
    return json.loads(file_content.decoded_content.decode("utf-8")), file_content.sha

def save_github_json(file_name, data, sha, message="Update"):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, message, json_string, sha)
    st.cache_data.clear()

# --- 3. UI 및 환경 설정 ---
st.set_page_config(page_title="Admin Panel", layout="wide")

# 카테고리 로드
categories, cat_sha = load_github_json("categories.json")

# 주소창 파라미터 제어 (뒤로가기용)
params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

# --- 4. 사이드바 (대분류 선택 및 편집) ---
st.sidebar.title("📁 대분류 관리")
category = st.sidebar.selectbox("카테고리 선택", categories)

st.sidebar.divider()
with st.sidebar.expander("🛠️ 명칭 편집/추가"):
    new_cat_name = st.text_input("새 카테고리 이름")
    if st.button("추가하기"):
        if new_cat_name and new_cat_name not in categories:
            categories.append(new_cat_name)
            save_github_json("categories.json", categories, cat_sha, "Add Category")
            st.rerun()
    
    st.divider()
    del_cat = st.selectbox("삭제할 카테고리", categories)
    if st.button("선택 삭제", help="주의: 카테고리 명칭만 삭제됩니다."):
        if len(categories) > 1:
            categories.remove(del_cat)
            save_github_json("categories.json", categories, cat_sha, "Delete Category")
            st.rerun()

# --- 5. 상세 페이지 화면 ---
if current_view == "detail" and selected_no:
    data, sha = load_github_json("data.json")
    post = next((item for item in data if str(item['no']) == str(selected_no)), None)
    
    if post:
        if st.button("⬅️ 목록으로 돌아가기"):
            st.query_params.clear()
            st.rerun()
        st.title(f"📖 {post['title']}")
        st.info(post['content'])
        st.caption(f"No: {post['no']} | 카테고리: {category}")
    else:
        st.error("글을 찾을 수 없습니다.")

# --- 6. 글쓰기 화면 ---
elif current_view == "write":
    st.title(f"📝 {category} - 새 글 작성")
    data, sha = load_github_json("data.json")
    
    with st.form("write_form"):
        title = st.text_input("제목")
        content = st.text_area("내용", height=300)
        if st.form_submit_button("저장하기"):
            new_no = max([int(i['no']) for i in data]) + 1 if data else 1
            # 글 저장 시 현재 선택된 카테고리 정보도 함께 저장
            data.insert(0, {"no": new_no, "title": title, "name": "관리자", "content": content, "viewcnt": 0, "category": category})
            save_github_json("data.json", data, sha, "Add Post")
            st.query_params.clear()
            st.rerun()
    if st.button("취소"):
        st.query_params.clear()
        st.rerun()

# --- 7. 메인 목록 화면 ---
else:
    st.title(f"👤 {category}")
    data, sha = load_github_json("data.json")

    # 필터링: 선택된 카테고리의 글만 보여주기 (옵션)
    # 만약 모든 글을 다 보여주려면 아래 두 줄을 주석 처리하세요.
    filtered_data = [item for item in data if item.get('category') == category]
    
    col_search, col_write = st.columns([3, 1])
    with col_search:
        search_all = st.checkbox("모든 카테고리 글 보기", value=False)
        display_data = data if search_all else filtered_data
        search_query = st.text_input("🔍 검색", placeholder="제목 키워드 입력...")
        
    with col_write:
        if st.button("📝 신규 행 추가", use_container_width=True):
            st.query_params.update(view="write")
            st.rerun()

    st.divider()
    # 테이블 헤더
    cols_h = st.columns([1, 6, 2, 1])
    for i, h in enumerate(["No", "Title", "Name", "Del"]):
        cols_h[i].write(f"**{h}**")
    st.divider()

    for idx, item in enumerate(display_data):
        if search_query and search_query.lower() not in item['title'].lower():
            continue
            
        cols = st.columns([1, 6, 2, 1])
        cols[0].write(item['no'])
        if cols[1].button(item['title'], key=f"btn_{item['no']}", use_container_width=True):
            st.query_params.update(view="detail", no=item['no'])
            st.rerun()
        cols[2].write(item.get('name', '관리자'))
        if cols[3].button("🗑️", key=f"del_{item['no']}"):
            # 원본 data에서 삭제
            data = [i for i in data if i['no'] != item['no']]
            save_github_json("data.json", data, sha, "Delete Post")
            st.rerun()
