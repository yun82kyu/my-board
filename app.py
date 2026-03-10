import streamlit as st
import json
from github import Github

# --- 1. GitHub 연결 설정 (Secrets 참조) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 연결 오류: {e}")
    st.stop()

# --- 2. 데이터 로드/저장 함수 ---
@st.cache_data(show_spinner=False)
def load_json(file_name):
    try:
        content = repo.get_contents(file_name)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        # 파일이 없을 경우 초기값 설정
        if "categories" in file_name:
            return ["기본분류"], None
        return [], None

def save_json(file_name, data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    # 데이터 업데이트 후 GitHub에 푸시
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear() # 캐시를 비워 최신 데이터를 즉시 반영

# --- 3. 페이지 기본 설정 및 세션 초기화 ---
st.set_page_config(page_title="My Admin Board", layout="wide")

# 최신 데이터 불러오기
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 세션 상태 관리 (현재 모드 및 카테고리)
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 4. 좌측 사이드바 (내비게이션) ---
with st.sidebar:
    st.title("🚀 Navigation")
    
    # [화면 전환 버튼]
    col_nav1, col_nav2 = st.columns(2)
    if col_nav1.button("📋 게시판", key="nav_list", use_container_width=True, 
                        type="primary" if st.session_state.view_mode == "list" else "secondary"):
        st.session_state.view_mode = "list"
        st.rerun()
        
    if col_nav2.button("⚙️ 관리", key="nav_manage", use_container_width=True,
                        type="primary" if st.session_state.view_mode == "manage" else "secondary"):
        st.session_state.view_mode = "manage"
        st.rerun()
    
    st.divider()
    
    # [게시판 모드일 때만 카테고리 필터 표시]
    if st.session_state.view_mode == "list":
        st.subheader("📁 카테고리")
        for idx, cat in enumerate(categories):
            is_active = (st.session_state.current_cat == cat)
            if st.button(cat, key=f"side_cat_{idx}", use_container_width=True, 
                         type="primary" if is_active else "secondary"):
                st.session_state.current_cat = cat
                st.rerun()

# --- 5. 메인 화면 분기 로직 ---

# [A] 대분류 관리 센터
if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    
    # 1. 신규 분류 추가
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_cat = st.text_input("새로 만들 분류 이름을 입력하세요", key="m_add_input")
        if st.button("추가하기", key="m_add_btn", use_container_width=True):
            if new_cat and new_cat not in categories:
                categories.append(new_cat)
                save_json("categories.json", categories, cat_sha)
                st.success(f"'{new_cat}' 분류가 성공적으로 추가되었습니다.")
                st.rerun()
            elif new_cat in categories:
                st.warning("이미 존재하는 분류 이름입니다.")

    st.write("")

    # 2. 기존 분류 삭제 (비어있는 분류만 삭제 가능)
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        st.caption("※ 삭제하려는 분류 안에 게시글이 하나도 없어야 삭제가 가능합니다.")
        
        # 글이 0개인 카테고리만 필터링
        deletable = [c for c in categories if len([i for i in all_data if i.get('category') == c]) == 0]
        
        if not deletable:
            st.info("현재 삭제할 수 있는 빈 분류가 없습니다.")
        else:
            del_target = st.selectbox("삭제할 분류 선택", deletable, key="m_del_select", index=None, placeholder="분류를 고르세요")
            confirm = st.checkbox("정말로 삭제하시겠습니까?", key="m_del_confirm")
            
            if st.button("선택 분류 삭제 실행", key="m_del_btn", type="danger", use_container_width=True):
                if del_target and confirm:
                    if len(categories) > 1:
                        categories.remove(del_target)
                        save_json("categories.json", categories, cat_sha)
                        # 현재 보던 분류가 삭제되면 첫 번째 분류로 이동
                        if st.session_state.current_cat == del_target:
                            st.session_state.current_cat = categories[0]
                        st.rerun()
                    else:
                        st.error("최소 한 개의 분류는 남아있어야 합니다.")
                elif not confirm:
                    st.warning("삭제 확인 체크박스에 체크해 주세요.")

# [B] 게시판 목록 페이지
else:
    st.title(f"📍 {st.session_state.current_cat}")
    
    # 현재 선택된 카테고리 글만 필터링
    filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

    # 새 글 쓰기 폼
    with st.expander(f"📝 {st.session_state.current_cat}에 새 글 쓰기"):
        with st.form("main_write_form"):
            title = st.text_input("제목")
            content = st.text_area("내용") # AttributeError 해결 지점
            if st.form_submit_button("저장하기"):
                if title and content:
                    # 고유 번호 생성
                    new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                    all_data.insert(0, {
                        "no": new_no, 
                        "title": title, 
                        "content": content, 
                        "category": st.session_state.current_cat
                    })
                    save_json("data.json", all_data, data_sha)
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해 주세요.")

    st.divider()

    # 게시글 리스트 출력
    if not filtered_data:
        st.info(f"'{st.session_state.current_cat}' 분류에 작성된 글이 아직 없습니다.")
    else:
        for item in filtered_data:
            c1, c2, c3 = st.columns([0.8, 7, 1.2])
            c1.write(f"#{item['no']}")
            with c2:
                # 제목 클릭 시 내용을 간단히 보여줌
                if st.button(item['title'], key=f"title_{item['no']}", use_container_width=True):
                    st.info(item['content'])
            if c3.button("🗑️ 삭제", key=f"del_{item['no']}", use_container_width=True):
                all_data = [i for i in all_data if i['no'] != item['no']]
                save_json("data.json", all_data, data_sha)
                st.rerun()
