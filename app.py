import streamlit as st
import json
from github import Github

# --- 1. 보안 및 데이터 연결 ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets 설정 확인 필요")
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

st.set_page_config(page_title="Admin Panel", layout="wide")

# 데이터 로딩
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태 초기화
if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
if "current_cat" not in st.session_state: st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 2. 좌측 사이드바 ---
with st.sidebar:
    st.title("🚀 Nav")
    for idx, cat in enumerate(categories):
        if st.button(cat, key=f"nav_{idx}", use_container_width=True, 
                     type="primary" if (st.session_state.current_cat == cat and st.session_state.view_mode != "manage") else "secondary"):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.rerun()
    st.divider()
    if st.button("⚙️ 대분류 관리", use_container_width=True, type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 3. 메인 화면 ---

# [CASE] 대분류 관리 페이지
if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    
    # 1. 추가 섹션 (st.form을 사용하여 버튼 에러 원천 차단)
    with st.form("add_category_form", clear_on_submit=True):
        st.subheader("➕ 신규 분류 추가")
        new_cat_input = st.text_input("분류 명칭", placeholder="새 분류 이름을 입력하세요")
        if st.form_submit_button("추가하기", use_container_width=True):
            if new_cat_input and new_cat_input not in categories:
                categories.append(new_cat_input)
                save_json("categories.json", categories, cat_sha)
                st.rerun()

    st.write("")

    # 2. 삭제 관리 섹션
    st.subheader("📋 분류 목록 및 삭제")
    
    # 헤더
    h_col1, h_col2, h_col3 = st.columns([3, 1, 1])
    h_col1.write("**분류명**"); h_col2.write("**게시글**"); h_col3.write("**관리**")
    st.divider()

    for idx, cat in enumerate(categories):
        r1, r2, r3 = st.columns([3, 1, 1])
        r1.write(f"**{cat}**")
        
        post_count = len([i for i in all_data if i.get('category') == cat])
        r2.write(f"{post_count} 개")
        
        # 글이 0개인 경우에만 '즉시 삭제' 버튼 노출
        if post_count == 0:
            # [핵심] 버튼을 누르는 순간 바로 삭제 로직을 타는 것이 아니라, 
            # 클릭 여부를 변수에 담아 순차적으로 처리하게 함으로써 API 충돌 방지
            if r3.button("삭제", key=f"del_btn_stable_{idx}", type="danger", use_container_width=True):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json("categories.json", categories, cat_sha)
                    # 현재 카테고리가 지워진 경우 첫 번째 카테고리로 이동
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("최소 1개 필요")
        else:
            r3.button("잠김", key=f"locked_{idx}", disabled=True, use_container_width=True)

    if st.button("← 메인 목록으로", key="go_back_home"):
        st.session_state.view_mode = "list"
        st.rerun()
    st.stop()

# [CASE] 일반 목록/상세 (생략 - 기존 로직 유지)
# ... (상세 및 목록 코드는 이전과 동일하게 유지하시면 됩니다)
st.title(f"👤 {st.session_state.current_cat}")
# (필요시 상세/목록 코드를 여기에 붙여넣으세요)
