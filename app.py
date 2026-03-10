import streamlit as st
import json
import time
from github import Github

# --- 1. GitHub 설정 ---
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
        if "categories" in file_name: return ["기본분류"], None
        return [], None

def save_json(file_name, data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear()

# --- 2. 초기화 및 고유 런타임 ID 생성 ---
# 매 실행마다 변하는 ID를 생성하여 버튼 충돌을 방지합니다.
if "runtime_id" not in st.session_state:
    st.session_state.runtime_id = int(time.time())

st.set_page_config(page_title="My Admin Board", layout="wide")
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
if "current_cat" not in st.session_state: st.session_state.current_cat = categories[0]

# --- 3. 사이드바 ---
with st.sidebar:
    st.title("🚀 Navigation")
    for idx, cat in enumerate(categories):
        # 키값에 runtime_id를 섞어 중복 방지
        if st.button(f"📁 {cat}", key=f"sb_{cat}_{idx}_{st.session_state.runtime_id}", use_container_width=True):
            st.session_state.current_cat = cat
            st.session_state.view_mode = "list"
            st.query_params.clear()
            st.rerun()
    st.divider()
    if st.button("⚙️ 관리 센터", key=f"sb_admin_{st.session_state.runtime_id}", use_container_width=True):
        st.session_state.view_mode = "manage"
        st.rerun()

# --- 4. 메인 로직 ---

if st.session_state.view_mode == "manage":
    st.title("⚙️ 대분류 관리 센터")
    
    # [추가]
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", key=f"m_add_in_{st.session_state.runtime_id}")
        if st.button("추가하기", key=f"m_add_btn_{st.session_state.runtime_id}", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json("categories.json", categories, cat_sha)
                st.session_state.runtime_id = int(time.time()) # 실행 후 ID 갱신
                st.rerun()

    # [삭제 - 에러 발생 지점]
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        deletable = [c for c in categories if len([i for i in all_data if i.get('category') == c]) == 0]
        
        if not deletable:
            st.info("비어 있는 분류가 없습니다.")
        else:
            target = st.selectbox("삭제할 분류", deletable, key=f"m_del_sel_{st.session_state.runtime_id}")
            confirm = st.checkbox("정말로 삭제하시겠습니까?", key=f"m_del_chk_{st.session_state.runtime_id}")
            
            # 🔥 핵심: 버튼 키에 runtime_id를 부여하여 매번 새로운 위젯으로 인식하게 함
            if st.button("🔥 선택 분류 삭제 실행", key=f"m_del_exec_{st.session_state.runtime_id}", type="danger", use_container_width=True):
                if target and confirm:
                    categories.remove(target)
                    save_json("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == target:
                        st.session_state.current_cat = categories[0]
                    st.session_state.runtime_id = int(time.time()) # ID 갱신하여 이전 버튼 폐기
                    st.rerun()

    if st.button("⬅️ 돌아가기", key=f"m_exit_{st.session_state.runtime_id}"):
        st.session_state.view_mode = "list"
        st.rerun()
    st.stop()

# [목록 화면]
st.title(f"👤 {st.session_state.current_cat}")
filtered = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# 게시글 리스트 출력 (생략된 기존 로직에도 {st.session_state.runtime_id}를 key 뒤에 붙여주면 더 완벽합니다)
for item in filtered:
    c1, c2, c3 = st.columns([0.6, 6, 0.8])
    if c2.button(item['title'], key=f"p_t_{item['no']}_{st.session_state.runtime_id}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
    if c3.button("🗑️", key=f"p_d_{item['no']}_{st.session_state.runtime_id}"):
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha)
        st.session_state.runtime_id = int(time.time())
        st.rerun()
