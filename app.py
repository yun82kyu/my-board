import streamlit as st
import json
from github import Github

# --- 1. GitHub 설정 및 데이터 로드 함수 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 설정 오류: {e}")
    st.stop()

@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        # 파일이 없을 경우 기본값 생성
        if "categories" in file_name:
            return ["기본분류"], None
        return [], None

def save_json(file_name, data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear() # 캐시를 비워 즉시 반영

# --- 2. 페이지 초기 설정 ---
st.set_page_config(page_title="My Admin Board", layout="wide")

# 최신 데이터 불러오기
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태(Session State) 초기화
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 3. 사이드바 내비게이션 (고유 Key 부여) ---
with st.sidebar:
    st.title("🚀 Navigation")
    st.subheader("📁 카테고리")
    
    for idx, cat in enumerate(categories):
        # 키값 중복 방지를 위해 'sb_nav_' 접두사 사용
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode == "list")
        if st.button(f"📁 {cat}", key=f"sb_nav_{cat}_{idx}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.query_params.clear()
            st.rerun()
            
    st.divider()
    # 관리 센터 버튼
    if st.button("⚙️ 대분류 관리 센터", key="sb_admin_go", use_container_width=True,
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 4. 메인 화면 분기 (에러 방지 핵심) ---

# [CASE A] 대분류 관리 모드
if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    st.write("분류를 추가하거나 비어 있는 분류를 삭제할 수 있습니다.")
    
    # 1. 신규 분류 추가 섹션
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", key="manage_add_input")
        if st.button("분류 추가하기", key="manage_add_btn", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json("categories.json", categories, cat_sha)
                st.success(f"'{new_name}' 추가 완료!")
                st.rerun()
            elif new_name in categories:
                st.warning("이미 존재하는 이름입니다.")

    st.write("")
    
    # 2. 분류 삭제 섹션
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        # 게시글이 0개인 카테고리만 삭제 대상으로 필터링
        deletable_cats = [c for c in categories if len([i for i in all_data if i.get('category') == c]) == 0]
        
        if not deletable_cats:
            st.info("현재 삭제 가능한(글이 없는) 빈 분류가 없습니다.")
        else:
            target_cat = st.selectbox("삭제할 분류를 선택하세요", deletable_cats, key="manage_del_sel", index=None, placeholder="분류 선택...")
            confirm = st.checkbox("정말로 이 분류를 삭제하시겠습니까?", key="manage_del_chk")
            
            if st.button("🔥 선택 분류 삭제 실행", key="manage_del_exec", type="danger", use_container_width=True):
                if target_cat and confirm:
                    if len(categories) > 1:
                        categories.remove(target_cat)
                        save_json("categories.json", categories, cat_sha)
                        # 삭제된 분류를 보고 있었다면 기본값으로 이동
                        if st.session_state.current_cat == target_cat:
                            st.session_state.current_cat = categories[0]
                        st.rerun()
                    else:
                        st.error("최소 한 개의 분류는 남겨두어야 합니다.")
                elif not confirm:
                    st.warning("삭제 확인 체크박스에 체크해 주세요.")

    st.divider()
    if st.button("⬅️ 메인 게시판으로 돌아가기", key="manage_back_btn"):
        st.session_state.view_mode = "list"
        st.rerun()
        
    # 🌟 중요: 관리 모드일 때 아래의 게시판 코드가 생성되지 않도록 중단
    st.stop() 

# [CASE B] 게시글 상세 보기 모드
params = st.query_params
if params.get("view") == "detail":
    post_no = params.get("no")
    post = next((i for i in all_data if str(i['no']) == str(post_no)), None)
    if post:
        if st.button("⬅️ 목록으로", key="detail_back_btn"):
            st.query_params.clear()
            st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    st.stop()

# [CASE C] 일반 목록 모드 (기본 화면)
st.title(f"👤 {st.session_state.current_cat}")

# 현재 카테고리에 맞는 데이터 필터링
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# 상단 검색 및 추가 툴바
col_search, col_write = st.columns([5, 1.2])
search_q = col_search.text_input("", placeholder="🔍 제목 검색...", key="main_search", label_visibility="collapsed")

if col_write.button("📝 새 글 쓰기", key="main_write_btn", use_container_width=True):
    st.session_state.show_editor = not st.session_state.get("show_editor", False)

if st.session_state.get("show_editor", False):
    with st.form("write_form_key"):
        st.caption(f"📍 {st.session_state.current_cat} 분류에 저장됩니다.")
        nt = st.text_input("제목")
        nc = st.text_area("내용")
        if st.form_submit_button("저장하기"):
            if nt and nc:
                new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {
                    "no": new_no, "title": nt, "name": "관리자", 
                    "content": nc, "category": st.session_state.current_cat
                })
                save_json("data.json", all_data, data_sha)
                st.session_state.show_editor = False
                st.rerun()

st.write("")
# 게시판 테이블 헤더
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# 게시글 목록 출력
for item in filtered_data:
    if search_q and search_q.lower() not in item['title'].lower():
        continue
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    
    # 제목 버튼 (상세 페이지 이동)
    if c2.button(item['title'], key=f"post_title_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
        
    c3.write(item.get('name', '관리자'))
    
    # 개별 글 삭제 버튼
    if c4.button("🗑️", key=f"post_del_{item['no']}"):
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha)
        st.rerun()
