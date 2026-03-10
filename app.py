import streamlit as st
import json
from github import Github

# --- 1. 설정 및 데이터 처리 ---
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

# --- 2. 환경 설정 ---
st.set_page_config(page_title="Admin", layout="wide")
params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

# 카테고리 로드
categories, cat_sha = load_json("categories.json")

# 현재 선택된 카테고리 관리 (세션)
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0]

# --- 3. 상단 대분류 메뉴 (버튼 나열 방식) ---
st.write("### 📁 대분류")
cat_cols = st.columns(len(categories) + 1)
for i, cat_name in enumerate(categories):
    # 현재 선택된 카테고리는 강조 효과
    btn_type = "primary" if st.session_state.current_cat == cat_name else "secondary"
    if cat_cols[i].button(cat_name, key=f"cat_{i}", type=btn_type, use_container_width=True):
        st.session_state.current_cat = cat_name
        st.query_params.clear()
        st.rerun()

# 카테고리 추가 기능 (작게)
with cat_cols[-1].popover("➕"):
    new_cat = st.text_input("새 분류명")
    if st.button("추가"):
        categories.append(new_cat)
        save_json("categories.json", categories, cat_sha)
        st.rerun()

st.divider()

# --- 4. 상세 페이지 ---
if current_view == "detail" and selected_no:
    data, sha = load_json("data.json")
    post = next((i for i in data if str(i['no']) == str(selected_no)), None)
    if post:
        st.button("⬅️ 목록", on_click=lambda: st.query_params.clear())
        st.subheader(post['title'])
        st.info(post['content'])
    st.stop()

# --- 5. 글쓰기 폼 (작게 숨김) ---
if current_view == "write":
    data, sha = load_json("data.json")
    with st.form("write_form"):
        st.caption(f"📍 {st.session_state.current_cat}에 글 쓰기")
        t = st.text_input("제목")
        c = st.text_area("내용")
        if st.form_submit_button("저장"):
            new_no = max([int(i['no']) for i in data]) + 1 if data else 1
            data.insert(0, {"no": new_no, "title": t, "name": "관리자", "content": c, "viewcnt": 0, "category": st.session_state.current_cat})
            save_json("data.json", data, sha)
            st.query_params.clear()
            st.rerun()
    if st.button("취소"): st.query_params.clear(); st.rerun()
    st.stop()

# --- 6. 메인 목록 (한 줄 레이아웃) ---
data, sha = load_json("data.json")
# 선택된 카테고리 글만 필터링
display_data = [i for i in data if i.get('category') == st.session_state.current_cat]

# 검색과 버튼을 한 줄로
search_col, btn_col = st.columns([5, 1])
search_query = search_col.text_input("", placeholder="🔍 현재 분류 내 제목 검색 (결과는 하단 표에 자동 반영)", label_visibility="collapsed")
if btn_col.button("📝 행 추가", use_container_width=True):
    st.query_params.update(view="write")
    st.rerun()

st.write("") # 간격 조절

# 테이블 헤더 (폭 조절)
# [No(0.5), Title(6), Name(1.5), Del(1)] 비중으로 좁게 설정
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**")
h2.write("**Title**")
h3.write("**Name**")
h4.write("**Del**")
st.markdown("<hr style='margin:0; padding:0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# 목록 출력
for item in display_data:
    if search_query and search_query.lower() not in item['title'].lower():
        continue
        
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    if c2.button(item['title'], key=f"t_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
    c3.write(item.get('name', '관리자'))
    if c4.button("🗑️", key=f"d_{item['no']}"):
        data = [i for i in data if i['no'] != item['no']]
        save_json("data.json", data, sha)
        st.rerun()
