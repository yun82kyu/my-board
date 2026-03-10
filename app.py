import streamlit as st
import json
from github import Github

# --- 1. GitHub 연결 설정 ---
try:
    # Secrets에 저장된 정보를 가져옵니다.
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
        return [], None

def save_json(file_name, data, sha):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    repo.update_file(file_name, "Update Data", json_string, sha)
    st.cache_data.clear() # 반영을 위해 캐시 삭제

# --- 3. 데이터 준비 ---
st.set_page_config(page_title="Test Board", layout="wide")
st.title("📝 테스트 게시판 (기본형)")

all_data, data_sha = load_json("data.json")

# --- 4. 글쓰기 기능 (에러 방지를 위해 간단한 구조) ---
with st.expander("➕ 새 글 작성하기", expanded=False):
    with st.form("simple_write_form"):
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
                    "category": "기본분류"
                })
                save_json("data.json", all_data, data_sha)
                st.success("저장되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해주세요.")

st.divider()

# --- 5. 목록 출력 ---
if not all_data:
    st.info("작성된 글이 없습니다.")
else:
    for item in all_data:
        # 각 행을 구분하는 유니크한 키 부여
        col1, col2, col3 = st.columns([1, 8, 1])
        col1.write(f"#{item['no']}")
        
        # 상세 보기는 일단 제목 클릭 시 텍스트 노출로 대체 (에러 변수 제거)
        with col2:
            if st.button(item['title'], key=f"btn_title_{item['no']}", use_container_width=True):
                st.info(item['content'])
        
        # 삭제 버튼
        if col3.button("🗑️", key=f"btn_del_{item['no']}"):
            all_data = [i for i in all_data if i['no'] != item['no']]
            save_json("data.json", all_data, data_sha)
            st.rerun()
