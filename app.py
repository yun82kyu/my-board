import streamlit as st
import json
from github import Github

# --- 1. 설정 및 데이터 로드 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def load_data():
    file_content = repo.get_contents("data.json")
    return json.loads(file_content.decoded_content.decode("utf-8")), file_content.sha

def save_data(data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file("data.json", "Update data", json_string, sha)

# --- 2. 레이아웃 설정 ---
st.set_page_config(page_title="LLM Study Admin", layout="wide")

# CSS로 이미지와 비슷한 느낌 주기 (폰트 및 간격)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 상단 메뉴 (이미지의 검은색 바 느낌)
st.sidebar.title("📁 대분류")
category = st.sidebar.radio("메뉴 선택", ["LLM(Large Language Model)", "OOP", "WAS", "Framework", "Data Science"])

# 세션 상태
if "view" not in st.session_state:
    st.session_state.view = "list"

# --- 3. 상세 페이지 ---
if st.session_state.view == "detail":
    post = st.session_state.selected_post
    if st.button("⬅️ Back to List"):
        st.session_state.view = "list"
        st.rerun()
    st.divider()
    st.subheader(f"📌 {post['title']}")
    st.info(post['content'])
    st.caption(f"No: {post['no']} | 작성자: {post['name']} | 조회수: {post['viewcnt']}")

# --- 4. 메인 목록 페이지 ---
else:
    st.title(f"👤 {category}")

    data, sha = load_data()

    # 상단 검색 및 글쓰기 버튼 영역
    col_search, col_write = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search", placeholder="검색어를 입력하세요...")
    with col_write:
        if st.button("📝 신규 행 추가", use_container_width=True):
            st.session_state.view = "write"

    # 글쓰기 모드 (행 추가)
    if st.session_state.view == "write":
        with st.form("new_row"):
            c1, c2 = st.columns(2)
            with c1: no = st.number_input("No", value=max([int(i['no']) for i in data])+1 if data else 1)
            with c2: title = st.text_input("Title")
            content = st.text_area("Content")
            if st.form_submit_button("저장하기"):
                data.insert(0, {"no": no, "title": title, "name": "관리자", "viewcnt": 0, "content": content})
                save_data(data, sha)
                st.session_state.view = "list"
                st.rerun()
        if st.button("취소"): 
            st.session_state.view = "list"
            st.rerun()

    st.divider()

    # 이미지와 유사한 테이블 헤더
    h_col = st.columns([1, 6, 2, 1, 1])
    h_col[0].write("**No**")
    h_col[1].write("**Title**")
    h_col[2].write("**Name**")
    h_col[3].write("**Viewcnt**")
    h_col[4].write("**Del**")
    st.divider()

    # 데이터 리스트 (필터링 적용)
    for idx, item in enumerate(data):
        if search_query and search_query not in item['title']:
            continue
            
        cols = st.columns([1, 6, 2, 1, 1])
        cols[0].write(item['no'])
        
        # 제목 클릭시 상세페이지 이동
        if cols[1].button(item['title'], key=f"t_{idx}", use_container_width=True):
            st.session_state.selected_post = item
            st.session_state.view = "detail"
            st.rerun()
            
        cols[2].write(item.get('name', '관리자'))
        cols[3].write(item.get('viewcnt', 0))
        
        if cols[4].button("❌", key=f"d_{idx}"):
            data.pop(idx)
            save_data(data, sha)
            st.rerun()

    # 하단 페이지네이션 느낌 (흉내만 냄)
    st.markdown("<center> 1 2 3 </center>", unsafe_allow_html=True)
