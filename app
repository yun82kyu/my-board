import streamlit as st
import json
from github import Github
import os

# --- 1. 보안 설정 (나중에 Streamlit 설정창에 입력할 값) ---
# 로컬 테스트용이 아닌 서버 배포용 설정입니다.
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] # 예: "내아이디/my-board"
except:
    st.error("Streamlit Secrets 설정이 필요합니다.")
    st.stop()

# GitHub 연결
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def get_json_from_github():
    file_content = repo.get_contents("data.json")
    return json.loads(file_content.decoded_content.decode("utf-8")), file_content.sha

def update_github_json(new_data, sha):
    json_string = json.dumps(new_data, indent=4, ensure_ascii=False)
    repo.update_file("data.json", "Update board data via Streamlit", json_string, sha)

# --- 2. 게시판 화면 UI ---
st.title("🚀 LLM 관리자 자동 게시판")

menu = st.sidebar.selectbox("메뉴", ["목록보기", "글쓰기"])

if menu == "목록보기":
    data, sha = get_json_from_github()
    for idx, item in enumerate(data):
        cols = st.columns([1, 4, 1])
        cols[0].write(item['no'])
        cols[1].write(item['title'])
        if cols[2].button("삭제", key=f"del_{idx}"):
            data.pop(idx)
            update_github_json(data, sha)
            st.success("삭제 성공! 깃허브 반영 중...")
            st.rerun()

elif menu == "글쓰기":
    with st.form("write_form"):
        no = st.number_input("번호", value=1000)
        title = st.text_input("제목")
        content = st.text_area("내용")
        if st.form_submit_button("등록하기"):
            data, sha = get_json_from_github()
            new_post = {"no": no, "title": title, "name": "관리자", "viewcnt": 0, "content": content}
            data.insert(0, new_post)
            update_github_json(data, sha)
            st.success("등록 성공! 깃허브에 데이터가 즉시 저장되었습니다.")
            st.balloons()
