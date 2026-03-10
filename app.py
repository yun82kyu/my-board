import streamlit as st
import json
from github import Github
from datetime import datetime

st.set_page_config(page_title="My Board", layout="wide")

# -------------------------
# GitHub 연결
# -------------------------
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo(st.secrets["REPO_NAME"])


# -------------------------
# JSON 로드
# -------------------------
def load_json(file):

    try:
        content = repo.get_contents(file)
        data = json.loads(content.decoded_content.decode())
        return data, content.sha

    except:
        return [], None


# -------------------------
# JSON 저장
# -------------------------
def save_json(file, data, sha):

    content = json.dumps(data, indent=4, ensure_ascii=False)

    try:
        if sha:
            repo.update_file(file, "update", content, sha)
        else:
            repo.create_file(file, "create", content)

    except:
        content_file = repo.get_contents(file)
        repo.update_file(file, "update", content, content_file.sha)


# -------------------------
# 데이터 로드
# -------------------------
categories, cat_sha = load_json("data/categories.json")
posts, post_sha = load_json("data/posts.json")


# -------------------------
# 세션 상태
# -------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "board"

if "category" not in st.session_state:
    st.session_state.category = categories[0]


# -------------------------
# 사이드바
# -------------------------
with st.sidebar:

    st.title("📚 Board")

    if st.button("📋 게시판"):
        st.session_state.mode = "board"
        st.rerun()

    if st.button("⚙️ 관리"):
        pw = st.text_input("관리자 비밀번호", type="password")

        if pw == st.secrets["ADMIN_PASSWORD"]:
            st.session_state.mode = "admin"
            st.rerun()

    st.divider()

    if st.session_state.mode == "board":

        st.subheader("카테고리")

        for c in categories:

            if st.button(c):
                st.session_state.category = c
                st.rerun()


# -------------------------
# 관리자 모드
# -------------------------
if st.session_state.mode == "admin":

    st.title("⚙️ 관리자 센터")

    new_cat = st.text_input("새 카테고리")

    if st.button("추가"):

        if new_cat not in categories:

            categories.append(new_cat)

            save_json(
                "data/categories.json",
                categories,
                cat_sha
            )

            st.success("추가 완료")
            st.rerun()

    st.subheader("카테고리 삭제")

    for c in categories:

        if st.button(f"{c} 삭제"):

            categories.remove(c)

            save_json(
                "data/categories.json",
                categories,
                cat_sha
            )

            st.rerun()


# -------------------------
# 게시판
# -------------------------
else:

    st.title(f"📂 {st.session_state.category}")

    # 글쓰기
    with st.expander("✏️ 글쓰기"):

        title = st.text_input("제목")
        content = st.text_area("내용")

        if st.button("등록"):

            no = max([p["no"] for p in posts], default=0) + 1

            posts.insert(0, {

                "no": no,
                "title": title,
                "content": content,
                "category": st.session_state.category,
                "views": 0,
                "date": str(datetime.now())[:16]

            })

            save_json(
                "data/posts.json",
                posts,
                post_sha
            )

            st.rerun()

    st.divider()

    filtered = [
        p for p in posts
        if p["category"] == st.session_state.category
    ]

    for p in filtered:

        col1, col2, col3 = st.columns([1,6,2])

        col1.write(p["no"])

        if col2.button(p["title"], key=f"title{p['no']}"):

            p["views"] += 1

            save_json(
                "data/posts.json",
                posts,
                post_sha
            )

            st.write(p["content"])
            st.caption(f"조회수 {p['views']} | {p['date']}")

        if col3.button("삭제", key=f"del{p['no']}"):

            posts = [
                x for x in posts
                if x["no"] != p["no"]
            ]

            save_json(
                "data/posts.json",
                posts,
                post_sha
            )

            st.rerun()
