import streamlit as st
import json
from github import Github

# --- 1. 보안 및 데이터 연결 (GitHub 전용) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정(GITHUB_TOKEN, REPO_NAME)이 필요합니다.")
    st.stop()

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return ([] if "data" in file_name else ["기본분류"]), None

def save_json(file_name, data_to_save, sha):
    json_string = json.dumps(data_to_save, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update", json_string, sha)
    st.cache_data.clear()

# --- 2. 기본 페이지 설정 ---
st.set_page_config(page_title="Category Manager", layout="wide")

# 데이터 로딩
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태 초기화 (페이지 모드 및 현재 카테고리)
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list" # list(목록), manage(관리), detail(상세)
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 3. 좌측 사이드바 (내비게이션) ---
with st.sidebar:
    st.title("🚀 Navigation")
    
    # 일반 카테고리 이동 버튼들
    st.subheader("📁 카테고리")
    for idx, cat in enumerate(categories):
        is_active = (st.session_state.current_cat == cat and st.session_state.view_mode != "manage")
        if st.button(cat, key=f"nav_{idx}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.rerun()
            
    st.divider()
    
    # 관리자 전용 버튼
    if st.button("⚙️ 대분류 관리 페이지", use_container_width=True, 
                 type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 4. 메인 화면 로직 분기 ---

# CASE 1: 대분류 관리 페이지 (사용자님이 요청하신 별도 관리 영역)
if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    st.info("이곳에서 대분류를 추가하거나 삭제할 수 있습니다. (내용이 있는 분류는 안전을 위해 삭제가 제한됩니다.)")
    
    # [1] 신규 추가 섹션
    with st.container(border=True):
        st.subheader("➕ 신규 대분류 생성")
        c1, c2 = st.columns([4, 1])
        new_cat_input = c1.text_input("새로운 분류 명칭을 입력하세요", placeholder="예: 자유게시판, 공지사항", label_visibility="collapsed")
        if c2.button("분류 추가", use_container_width=True):
            if new_cat_input and new_cat_input not in categories:
                categories.append(new_cat_input)
                save_json("categories.json", categories, cat_sha)
                st.success(f"'{new_cat_input}' 분류가 추가되었습니다.")
                st.rerun()
            else:
                st.warning("이미 존재하거나 유효하지 않은 이름입니다.")

    st.write("")

    # [2] 목록 및 삭제 관리 섹션
    st.subheader("📋 대분류 리스트")
    # 테이블 헤더 스타일
    th1, th2, th3 = st.columns([3, 1, 1])
    th1.write("**분류 명칭**")
    th2.write("**등록된 글 수**")
    th3.write("**관리**")
    st.divider()

    for idx, cat in enumerate(categories):
        r1, r2, r3 = st.columns([3, 1, 1])
        r1.write(f"**{cat}**")
        
        # 실제 글 개수 파악
        post_count = len([i for i in all_data if i.get('category') == cat])
        r2.write(f"{post_count} 개")
        
        # 조건부 삭제 기능
        if post_count == 0:
            if r3.button("즉시 삭제", key=f"manage_del_{idx}", type="danger", use_container_width=True):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("최소 1개의 분류는 유지해야 합니다.")
        else:
            # 글이 있으면 삭제 버튼 비활성화 (보안)
            r3.button("삭제 불가", key=f"manage_del_{idx}", disabled=True, use_container_width=True, help="분류 내 글을 먼저 삭제해주세요.")

# CASE 2: 상세 내용 보기
elif st.session_state.view_mode == "detail":
    params = st.query_params
    selected_no = params.get("no")
    post = next((i for i in all_data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록으로 돌아가기"):
            st.session_state.view_mode = "list"
            st.rerun()
        st.divider()
        st.title(post['title'])
        st.caption(f"분류: {post['category']} | No: {post['no']}")
        st.info(post['content'])

# CASE 3: 일반 목록 보기 (메인 페이지)
else:
    st.title(f"👤 {st.session_state.current_cat}")
    
    # 필터링
    filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]
    
    # 상단 도구 (검색 및 글쓰기)
    s_col, w_col = st.columns([5, 1.2])
    search_q = s_col.text_input("", placeholder="🔍 제목으로 검색...", label_visibility="collapsed")
    
    if w_col.button("📝 새 글 쓰기", use_container_width=True):
        st.session_state.show_editor = not st.session_state.get("show_editor", False)

    if st.session_state.get("show_editor", False):
        with st.form("editor_form"):
            et = st.text_input("제목")
            ec = st.text_area("내용")
            if st.form_submit_button("저장하기"):
                if et and ec:
                    new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                    all_data.insert(0, {"no": new_no, "title": et, "name": "관리자", "content": ec, "category": st.session_state.current_cat})
                    save_json("data.json", all_data, data_sha)
                    st.session_state.show_editor = False
                    st.rerun()

    st.write("")
    # 리스트 헤더
    h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
    h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
    st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

    for item in filtered_data:
        if search_q and search_q.lower() not in item['title'].lower():
            continue
        c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
        c1.write(item['no'])
        if c2.button(item['title'], key=f"p_{item['no']}", use_container_width=True):
            st.query_params.update(no=item['no'])
            st.session_state.view_mode = "detail"
            st.rerun()
        c3.write(item.get('name', '관리자'))
        if c4.button("🗑️", key=f"del_row_{item['no']}"):
            all_data = [i for i in all_data if i['no'] != item['no']]
            save_json("data.json", all_data, data_sha)
            st.rerun()
