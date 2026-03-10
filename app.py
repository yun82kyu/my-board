import streamlit as st
import json
from github import Github
# 분리한 파일에서 함수 불러오기
from category_manager import show_category_manager

# --- 1. GitHub 보안 설정 및 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 설정 확인 필요: {e}")
    st.stop()

# --- 2. 데이터 로드/저장 함수 ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        # 파일이 없으면 기본값 반환
        if "categories" in file_name:
            return ["기본분류"], None
        return [], None

def save_json(file_name, data_to_save, sha):
    json_string = json.dumps(data_to_save, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear() # 캐시 초기화 (새로운 데이터를 불러오기 위함)

# --- 3. 기본 페이지 설정 및 데이터 준비 ---
st.set_page_config(page_title="My Admin Board", layout="wide")

# 최신 데이터 불러오기
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태 초기화 (view_mode와 current_cat)
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 4. 좌측 사이드바 내비게이션 ---
with st.sidebar:
    st.title("🚀 Navigation")
    st.subheader("📁 카테고리 목록")
    
    # 카테고리 이동 버튼 생성
    for idx, cat in enumerate(categories):
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode == "list")
        if st.button(cat, key=f"nav_btn_{idx}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.query_params.clear() # 상세페이지 보고 있었다면 초기화
            st.rerun()
            
    st.divider()
    
    # [관리 페이지 이동 버튼]
    if st.button("⚙️ 대분류 관리 센터", use_container_width=True, 
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 5. 메인 화면 로직 (모드별 분기) ---

# [A] 대분류 관리 모드
if st.session_state.view_mode == "manage":
    # 컨테이너로 영역을 격리하여 렌더링 안정성 확보
    with st.container():
        show_category_manager(categories, cat_sha, all_data, save_json)
    
    # 실행 중단 (하단 목록 버튼들과의 충돌 방지)
    st.stop()

# [B] 상세 보기 모드 (URL 파라미터 기반)
params = st.query_params
if params.get("view") == "detail":
    selected_no = params.get("no")
    post = next((i for i in all_data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록으로"): 
            st.query_params.clear()
            st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    else:
        st.error("해당 글을 찾을 수 없습니다.")
        if st.button("목록으로"): st.query_params.clear(); st.rerun()
    st.stop() # 상세 모드에서도 여기서 중단

# [C] 일반 목록 모드 (기본 화면)
st.title(f"👤 {st.session_state.current_cat}")

# 해당 카테고리 글만 필터물
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# 상단 툴바 (검색 / 글쓰기)
search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", label_visibility="collapsed")

if write_c.button("📝 새 행 추가", use_container_width=True):
    st.session_state.show_editor = not st.session_state.get("show_editor", False)

# 글쓰기 폼
if st.session_state.get("show_editor", False):
    with st.form("main_write_form"):
        st.caption(f"📍 {st.session_state.current_cat} 분류에 저장됩니다.")
        nt = st.text_input("제목")
        nc = st.text_area("내용")
        if st.form_submit_button("저장하기"):
            if nt and nc:
                # 새 번호 생성 (역순 정렬을 위해 insert 0)
                new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {
                    "no": new_no, "title": nt, "name": "관리자", 
                    "content": nc, "category": st.session_state.current_cat
                })
                save_json("data.json", all_data, data_sha)
                st.session_state.show_editor = False
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해주세요.")

st.write("")
# 테이블 헤더
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# 게시글 목록 출력
for item in filtered_data:
    if search_q and search_q.lower() not in item['title'].lower():
        continue
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    
    # 제목 버튼 (클릭 시 URL 파라미터 변경)
    if c2.button(item['title'], key=f"post_btn_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
        
    c3.write(item.get('name', '관리자'))
    
    # 개별 글 삭제 버튼
    if c4.button("🗑️", key=f"del_row_{item['no']}"):
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha)
        st.rerun()
