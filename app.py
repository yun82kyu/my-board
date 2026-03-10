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

# 뒤로가기 지원을 위한 파라미터
params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

categories, cat_sha = load_json("categories.json")
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0]

# --- 3. 좌측 사이드바 (자동 접힘 기능 포함) ---
with st.sidebar:
    col_h1, col_h2 = st.columns([3, 1])
    col_h1.subheader("📁 대분류")
    with col_h2:
        # 추가 버튼을 누르고 데이터를 저장한 뒤 rerun하면 팝업이 자동으로 접힙니다.
        with st.popover("➕"):
            new_name = st.text_input("분류명 입력")
            if st.button("추가", use_container_width=True):
                if new_name and new_name not in categories:
                    categories.append(new_name)
                    save_json("categories.json", categories, cat_sha)
                    st.rerun() # ★ 여기서 화면을 새로고침하여 팝업을 닫습니다.

    st.divider()
    for cat in categories:
        is_sel = (st.session_state.current_cat == cat)
        if st.button(cat, key=f"s_{cat}", use_container_width=True, type="primary" if is_sel else "secondary"):
            st.session_state.current_cat = cat
            st.query_params.clear()
            st.rerun()

# --- 4. 메인 화면 - 상세 페이지 ---
if current_view == "detail" and selected_no:
    data, _ = load_json("data.json")
    post = next((i for i in data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록으로"): st.query_params.clear(); st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    st.stop()

# --- 5. 메인 화면 - 목록 (슬림 레이아웃) ---
st.title(f"👤 {st.session_state.current_cat}")

data, data_sha = load_json("data.json")
filtered_data = [i for i in data if i.get('category') == st.session_state.current_cat]

# [검색창 | 추가버튼] 한 줄 레이아웃
search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", label_visibility="collapsed")

# 신규 행 추가 버튼 (팝업 형태로 아주 작게 구현)
with write_c.popover("📝 신규 행 추가", use_container_width=True):
    with st.form("new_post"):
        new_t = st.text_input("제목")
        new_c = st.text_area("내용")
        if st.form_submit_button("저장"):
            new_no = max([int(i['no']) for i in data]) + 1 if data else 1
            data.insert(0, {"no": new_no, "title": new_t, "name": "관리자", "content": new_c, "viewcnt": 0, "category": st.session_state.current_cat})
            save_json("data.json", data, data_sha)
            st.rerun()

# 테이블 헤더 (폭을 아주 좁게 조정)
st.write("") 
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# 목록 데이터 출력
for item in filtered_data:
    if search_q and search_q.lower() not in item['title'].lower():
        continue
    
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    if c2.button(item['title'], key=f"t_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
    c3.write(item.get('name', '관리자'))
    if c4.button("🗑️", key=f"d_{item['no']}"):
        data = [i for i in data if i['no'] != item['no']]
        save_json("data.json", data, data_sha)
        st.rerun()
