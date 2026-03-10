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

@st.cache_data(show_spinner=False)
def load_data():
    file_content = repo.get_contents("data.json")
    return json.loads(file_content.decoded_content.decode("utf-8")), file_content.sha

def save_data(data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file("data.json", "Update data", json_string, sha)
    st.cache_data.clear() # 데이터 갱신 시 캐시 삭제

# --- 2. 레이아웃 및 주소창 제어 ---
st.set_page_config(page_title="LLM Study Admin", layout="wide")

# 주소창의 파라미터를 읽어서 현재 뷰(view) 결정
# 크롬 뒤로가기를 누르면 이 파라미터가 변하면서 화면이 바뀝니다.
params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

# --- 3. 사이드바 메뉴 ---
st.sidebar.title("📁 대분류")
category = st.sidebar.radio("메뉴 선택", ["LLM(Large Language Model)", "OOP", "WAS", "Framework", "Data Science"])

# --- 4. 상세 페이지 로직 ---
if current_view == "detail" and selected_no:
    data, sha = load_data()
    # 해당 번호의 글 찾기
    post = next((item for item in data if str(item['no']) == str(selected_no)), None)
    
    if post:
        if st.button("⬅️ Back to List"):
            st.query_params.clear() # 주소창 파라미터 삭제 (목록으로)
            st.rerun()
            
        st.divider()
        st.subheader(f"📌 {post['title']}")
        st.info(post['content'])
        st.caption(f"No: {post['no']} | 작성자: {post['name']} | 조회수: {post['viewcnt']}")
    else:
        st.error("글을 찾을 수 없습니다.")
        if st.button("목록으로 돌아가기"):
            st.query_params.clear()
            st.rerun()

# --- 5. 글쓰기 페이지 로직 ---
elif current_view == "write":
    st.title("📝 새 게시글 행 추가")
    data, sha = load_data()
    
    with st.form("new_row"):
        c1, c2 = st.columns(2)
        with c1: no = st.number_input("No", value=max([int(i['no']) for i in data])+1 if data else 1)
        with c2: title = st.text_input("Title")
        content = st.text_area("Content", height=300)
        
        if st.form_submit_button("저장하기"):
            data.insert(0, {"no": no, "title": title, "name": "관리자", "viewcnt": 0, "content": content})
            save_data(data, sha)
            st.query_params.clear() # 저장 후 목록으로
            st.rerun()
            
    if st.button("취소"):
        st.query_params.clear()
        st.rerun()

# --- 6. 메인 목록 페이지 로직 ---
else:
    st.title(f"👤 {category}")
    data, sha = load_data()

    col_search, col_write = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search", placeholder="검색어를 입력하세요...")
    with col_write:
        if st.button("📝 신규 행 추가", use_container_width=True):
            st.query_params.update(view="write") # 주소창에 ?view=write 추가
            st.rerun()

    st.divider()
    
    # 헤더
    h_col = st.columns([1, 6, 2, 1, 1])
    h_col[0].write("**No**")
    h_col[1].write("**Title**")
    h_col[2].write("**Name**")
    h_col[3].write("**Viewcnt**")
    h_col[4].write("**Del**")
    st.divider()

    for idx, item in enumerate(data):
        if search_query and search_query.lower() not in item['title'].lower():
            continue
            
        cols = st.columns([1, 6, 2, 1, 1])
        cols[0].write(item['no'])
        
        # 제목 클릭 시 주소창 파라미터 변경
        if cols[1].button(item['title'], key=f"t_{idx}", use_container_width=True):
            st.query_params.update(view="detail", no=item['no'])
            st.rerun()
            
        cols[2].write(item.get('name', '관리자'))
        cols[3].write(item.get('viewcnt', 0))
        
        if cols[4].button("❌", key=f"d_{idx}"):
            data.pop(idx)
            save_data(data, sha)
            st.rerun()

    st.markdown("<center style='color:gray;'>1 2 3</center>", unsafe_allow_html=True)
