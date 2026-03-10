import streamlit as st
import json
from github import Github

# --- 1. GitHub 연결 설정 ---
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
        # 파일이 없을 경우 기본값 반환
        if "categories" in file_name:
            return ["기본분류", "업무", "개인"], None
        return [], None

def save_json(file_name, data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear()

# --- 3. 데이터 준비 및 초기화 ---
st.set_page_config(page_title="Category Board", layout="wide")

# JSON 데이터 로드
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

# 현재 선택된 카테고리를 세션에 저장 (기본값은 첫 번째 카테고리)
if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0]

# --- 4. 좌측 사이드바 (분류 목록) ---
with st.sidebar:
    st.title("📁 분류 목록")
    st.write("보기 원하는 분류를 선택하세요.")
    
    for idx, cat in enumerate(categories):
        # 현재 선택된 카테고리는 강조 표시(primary)
        is_active = (st.session_state.current_cat == cat)
        if st.button(cat, key=f"side_cat_{idx}", use_container_width=True, 
                     type="primary" if is_active else "secondary"):
            st.session_state.current_cat = cat
            st.rerun()

# --- 5. 메인 화면 (선택된 카테고리 글만 표시) ---
st.title(f"📍 {st.session_state.current_cat}")

# 데이터 필터링: 현재 카테고리에 해당하는 글만 추출
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

# 글쓰기 기능 (필터링된 카테고리에 자동으로 저장되도록 설정)
with st.expander(f"➕ {st.session_state.current_cat}에 새 글 쓰기", expanded=False):
    with st.form("category_write_form"):
        title = st.text_input("제목")
        content = st.text_area("내용")
        submit = st.form_submit_button("저장하기")
        
        if submit:
            if title and content:
                new_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {
                    "no": new_no, 
                    "title": title, 
                    "content": content,
                    "category": st.session_state.current_cat  # 현재 선택된 카테고리 저장
                })
                save_json("data.json", all_data, data_sha)
                st.success("저장되었습니다!")
                st.rerun()

st.divider()

# 목록 출력
if not filtered_data:
    st.info(f"'{st.session_state.current_cat}' 분류에 작성된 글이 없습니다.")
else:
    for item in filtered_data:
        col1, col2, col3 = st.columns([1, 8, 1])
        col1.write(f"#{item['no']}")
        
        with col2:
            if st.button(item['title'], key=f"list_btn_{item['no']}", use_container_width=True):
                st.info(item['content'])
        
        if col3.button("🗑️", key=f"list_del_{item['no']}"):
            # 전체 데이터에서 해당 번호의 글 삭제
            all_data = [i for i in all_data if i['no'] != item['no']]
            save_json("data.json", all_data, data_sha)
            st.rerun()
