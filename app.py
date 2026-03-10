import streamlit as st
import json
from github import Github

# --- 1. 보안 설정 및 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정이 필요합니다. GITHUB_TOKEN과 REPO_NAME을 확인하세요.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- 2. 데이터 처리 함수 (안전한 로드/저장) ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        # 파일이 없을 경우 초기값 생성
        return [] if "data" in file_name else ["기본분류"], None

def save_json(file_name, data_to_save, sha, msg="Update"):
    json_string = json.dumps(data_to_save, indent=4, ensure_ascii=False)
    repo.update_file(file_name, msg, json_string, sha)
    st.cache_data.clear()

# --- 3. 기본 레이아웃 설정 ---
st.set_page_config(page_title="Admin Panel", layout="wide")

# 모든 데이터를 먼저 불러와서 오류 방지
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 현재 뷰 및 선택 번호 확인
params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

# 세션 상태 초기화
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 4. 좌측 사이드바 (분류 관리 및 삭제 확인) ---
with st.sidebar:
    col_h1, col_h2 = st.columns([3, 1])
    col_h1.subheader("📁 대분류")
    with col_h2:
        with st.popover("➕"):
            new_name = st.text_input("분류명 입력")
            if st.button("추가", use_container_width=True):
                if new_name and new_name not in categories:
                    categories.append(new_name)
                    save_json("categories.json", categories, cat_sha, "Add Category")
                    st.rerun()

    st.divider()
    
    for idx, cat in enumerate(categories):
        side_c1, side_c2 = st.columns([4, 1.2])
        
        # 1. 카테고리 선택 버튼
        is_sel = (st.session_state.current_cat == cat)
        if side_c1.button(cat, key=f"s_{cat}", use_container_width=True, type="primary" if is_sel else "secondary"):
            st.session_state.current_cat = cat
            st.query_params.clear()
            st.rerun()
            
        # 2. 안전한 삭제 (글 개수 체크 로직)
        with side_c2.popover("🗑️"):
            # 'all_data' 변수가 로드된 후이므로 안전하게 계산 가능
            post_count = len([i for i in all_data if i.get('category') == cat])
            
            if post_count > 0:
                st.warning(f"내용 {post_count}개 존재")
                st.write("삭제하시겠습니까?")
            else:
                st.write("삭제할까요?")
            
            if st.button("확인", key=f"confirm_del_{idx}", use_container_width=True, type="danger"):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json("categories.json", categories, cat_sha, "Delete Category")
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("삭제 불가")

# --- 5. 메인 화면 ---
# A. 상세 페이지
if current_view == "detail" and selected_no:
    post = next((i for i in all_data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록으로"): st.query_params.clear(); st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    else:
        st.error("데이터를 찾을 수 없습니다.")
    st.stop()

# B. 목록 페이지
st.title(f"👤 {st.session_state.current_cat}")

# 현재 카테고리 글만 필터링
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# 상단 검색 및 추가 한 줄 레이아웃
search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", label_visibility="collapsed")

with write_c.popover("📝 행 추가", use_container_width=True):
    with st.form("new_post", clear_on_submit=True):
        new_t = st.text_input("제목")
        new_c = st.text_area("내용")
        if st.form_submit_button("저장"):
            if new_t and new_c:
                new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {"no": new_no, "title": new_t, "name": "관리자", "content": new_c, "viewcnt": 0, "category": st.session_state.current_cat})
                save_json("data.json", all_data, data_sha, "Add Post")
                st.rerun()
            else:
                st.error("내용을 입력하세요.")

# 목록 출력
st.write("") 
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

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
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha, "Delete Post")
        st.rerun()
