import streamlit as st
import json
from github import Github
from datetime import datetime

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# GitHub 연결
# -----------------------------
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
except Exception as e:
    st.error(f"GitHub 연결 실패: {e}")
    st.stop()


# -----------------------------
# JSON 로드
# -----------------------------
def load_json(file):

    try:
        content = repo.get_contents(file)
        data = json.loads(content.decoded_content.decode("utf-8"))
        return data, content.sha

    except Exception:
        return [], None


# -----------------------------
# JSON 저장 (충돌 방지)
# -----------------------------
def save_json(file, data):

    json_string = json.dumps(data, indent=4, ensure_ascii=False)

    try:

        content = repo.get_contents(file)

        repo.update_file(
            file,
            "update data",
            json_string,
            content.sha
        )

    except Exception:

        repo.create_file(
            file,
            "create data",
            json_string
        )


# -----------------------------
# 데이터 불러오기
# -----------------------------
categories, cat_sha = load_json("categories.json")
posts, post_sha = load_json("data.json")

# 카테고리 없을 경우 생성
if not categories:
    categories = ["기본분류"]
    save_json("categories.json", categories)


# -----------------------------
# 세션 상태
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "board"

if "category" not in st.session_state:
    st.session_state.category = categories[0]

if "view_post" not in st.session_state:
    st.session_state.view_post = None


# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:

    st.title("📚 게시판")

    if st.button("📋 게시판"):
        st.session_state.mode = "board"
        st.session_state.view_post = None
        st.rerun()

    if st.button("⚙️ 관리"):
        pw = st.text_input("관리자 비밀번호", type="password")

        if pw == st.secrets.get("ADMIN_PASSWORD", "1234"):
            st.session_state.mode = "admin"
            st.rerun()

    st.divider()

    if st.session_state.mode == "board":

        st.subheader("카테고리")

        for c in categories:

            if st.button(c, use_container_width=True):

                st.session_state.category = c
                st.session_state.view_post = None
                st.rerun()


# -----------------------------
# 관리자 모드
# -----------------------------
if st.session_state.mode == "admin":

    st.title("⚙️ 카테고리 관리")

    st.subheader("카테고리 추가")

    new_cat = st.text_input("새 카테고리 이름")

    if st.button("추가"):

        if new_cat and new_cat not in categories:

            categories.append(new_cat)

            save_json(
                "categories.json",
                categories
            )

            st.success("카테고리 추가 완료")
            st.rerun()

        else:
            st.warning("이미 존재하거나 이름이 비어 있습니다")

    st.divider()

    st.subheader("카테고리 삭제")

    for c in categories:

        if st.button(f"{c} 삭제"):

            # 게시글 있는지 확인
            count = len([p for p in posts if p["category"] == c])

            if count > 0:
                st.error("게시글이 있는 카테고리는 삭제 불가")
            else:

                categories.remove(c)

                save_json(
                    "categories.json",
                    categories
                )

                st.rerun()


# -----------------------------
# 게시판
# -----------------------------
else:

    st.title(f"📂 {st.session_state.category}")

    # -------------------------
    # 글쓰기
    # -------------------------
    with st.expander("✏️ 글쓰기"):

        title = st.text_input("제목")
        content = st.text_area("내용")

        if st.button("등록"):

            if title and content:

                new_no = max([p["no"] for p in posts], default=0) + 1

                posts.insert(0, {

                    "no": new_no,
                    "title": title,
                    "content": content,
                    "category": st.session_state.category,
                    "views": 0,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")

                })

                save_json(
                    "data.json",
                    posts
                )

                st.rerun()

            else:
                st.warning("제목과 내용을 입력하세요")

    st.divider()

    # -------------------------
    # 게시글 필터
    # -------------------------
    filtered_posts = [

        p for p in posts
        if p["category"] == st.session_state.category
    ]

    if not filtered_posts:
        st.info("게시글이 없습니다")

    # -------------------------
    # 게시글 리스트
    # -------------------------
    for p in filtered_posts:

        col1, col2, col3 = st.columns([1,6,2])

        col1.write(p["no"])

        if col2.button(p["title"], key=f"title_{p['no']}"):

            st.session_state.view_post = p["no"]

            p["views"] += 1

            save_json(
                "data.json",
                posts
            )

            st.rerun()

        if col3.button("삭제", key=f"del_{p['no']}"):

            posts = [

                x for x in posts
                if x["no"] != p["no"]
            ]

            save_json(
                "data.json",
                posts
            )

            st.rerun()

    # -------------------------
    # 게시글 보기
    # -------------------------
    if st.session_state.view_post:

        post = next(
            (p for p in posts if p["no"] == st.session_state.view_post),
            None
        )

        if post:

            st.divider()

            st.subheader(post["title"])

            st.write(post["content"])

            st.caption(
                f"조회수 {post['views']} | {post['date']}"
            )
