import streamlit as st
import json
from github import Github
from datetime import datetime
import time

st.set_page_config(page_title="My Board", layout="wide")

# -----------------------------
# 1. GitHub 연결
# -----------------------------
if "repo" not in st.session_state:
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        st.session_state.repo = g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

# -----------------------------
# 2. 데이터 로드
# -----------------------------
@st.cache_data(ttl=300)
def load_json(file):
    try:
        content = st.session_state.repo.get_contents(file)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except:
        return [], None


def save_json(file, data):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)

    try:
        curr = st.session_state.repo.get_contents(file)
        st.session_state.repo.update_file(file, "update data", json_string, curr.sha)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"저장 오류: {e}")

# -----------------------------
# 3. 이미지 업로드
# -----------------------------
def upload_image(file):

    try:
        file_name = f"uploads/{int(time.time())}_{file.name}"

        content = file.read()

        st.session_state.repo.create_file(
            file_name,
            "upload image",
            content
        )

        url = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/{file_name}"

        return url

    except Exception as e:
        st.error(f"이미지 업로드 실패: {e}")
        return ""

# -----------------------------
# 초기 데이터 로드
# -----------------------------
if "categories" not in st.session_state:
    cats, _ = load_json("categories.json")
    st.session_state.categories = cats if cats else ["기본분류"]

if "posts" not in st.session_state:
    pts, _ = load_json("data.json")
    st.session_state.posts = pts if pts else []

# -----------------------------
# 세션 상태
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "board"

if "view_post" not in st.session_state:
    st.session_state.view_post = None

if "write_mode" not in st.session_state:
    st.session_state.write_mode = False

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "category" not in st.session_state:
    st.session_state.category = st.session_state.categories[0]

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:

    st.title("📚 Fast Board")

    c1, c2 = st.columns(2)

    if c1.button("📋 게시판", use_container_width=True):
        st.session_state.mode = "board"
        st.session_state.view_post = None
        st.session_state.write_mode = False
        st.session_state.edit_mode = False
        st.rerun()

    if c2.button("⚙️ 관리", use_container_width=True):
        st.session_state.mode = "admin"
        st.rerun()

    st.divider()

    st.subheader("📁 카테고리")

    for idx, c in enumerate(st.session_state.categories):

        if st.button(
            c,
            key=f"side_{idx}",
            use_container_width=True,
            type="primary" if st.session_state.category == c else "secondary"
        ):

            st.session_state.category = c
            st.session_state.mode = "board"
            st.session_state.view_post = None
            st.session_state.write_mode = False
            st.rerun()

# -----------------------------
# 관리자 모드
# -----------------------------
if st.session_state.mode == "admin":

    st.title("⚙️ 카테고리 관리")

    with st.container(border=True):

        st.subheader("➕ 추가")

        new_cat = st.text_input("새 카테고리")

        if st.button("추가 실행"):

            if new_cat and new_cat not in st.session_state.categories:

                st.session_state.categories.append(new_cat)

                save_json("categories.json", st.session_state.categories)

                st.rerun()

    with st.container(border=True):

        st.subheader("🗑️ 삭제")

        del_target = st.selectbox("삭제할 대상", st.session_state.categories)

        if st.button("삭제 실행"):

            if len(st.session_state.categories) > 1:

                st.session_state.categories.remove(del_target)

                save_json("categories.json", st.session_state.categories)

                st.rerun()

            else:
                st.error("최소 1개는 필요합니다.")

# -----------------------------
# 게시판 모드
# -----------------------------
else:

    # -------------------------
    # 글쓰기 페이지
    # -------------------------
    if st.session_state.write_mode:

        st.title("📝 새 게시글 작성")

        w_title = st.text_input("제목")

        w_content = st.text_area("내용", height=300)

        uploaded_imgs = st.file_uploader(
            "이미지 업로드",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

        col_w1, col_w2 = st.columns(2)

        if col_w1.button("💾 저장하기", use_container_width=True, type="primary"):

            new_no = max(
                [p.get("no", 0) for p in st.session_state.posts],
                default=0
            ) + 1

            img_urls = []

            if uploaded_imgs:

                for img in uploaded_imgs:

                    url = upload_image(img)

                    if url:
                        img_urls.append(url)

            st.session_state.posts.insert(0, {

                "no": new_no,
                "title": w_title,
                "content": w_content,
                "images": img_urls,
                "category": st.session_state.category,
                "date": datetime.now().strftime("%Y-%m-%d")

            })

            save_json("data.json", st.session_state.posts)

            st.session_state.write_mode = False

            st.rerun()

        if col_w2.button("❌ 취소", use_container_width=True):

            st.session_state.write_mode = False

            st.rerun()

    # -------------------------
    # 게시글 보기
    # -------------------------
    elif st.session_state.view_post:

        post = next(
            (p for p in st.session_state.posts if p["no"] == st.session_state.view_post),
            None
        )

        if post:

            st.title(post["title"])

            st.caption(f"📅 {post.get('date')} | 📂 {post.get('category')}")

            st.divider()

            st.markdown(post["content"])

            if post.get("images"):

                st.divider()

                for img in post["images"]:

                    st.image(img)

            st.divider()

            if st.button("🔙 목록으로"):

                st.session_state.view_post = None

                st.rerun()

    # -------------------------
    # 게시글 목록
    # -------------------------
    else:

        st.title(f"📂 {st.session_state.category}")

        if st.button("➕ 새 글 추가"):

            st.session_state.write_mode = True

            st.rerun()

        st.divider()

        filtered = [

            p for p in st.session_state.posts

            if p.get("category") == st.session_state.category

        ]

        if not filtered:

            st.info("글이 없습니다.")

        else:

            h1, h2, h3 = st.columns([1, 7, 1.5])

            h1.write("**번호**")

            h2.write("**제목**")

            h3.write("**관리**")

            for p in filtered:

                col1, col2, col3 = st.columns([1, 7, 1.5])

                col1.write(f"{p['no']}")

                if col2.button(
                    p["title"],
                    key=f"list_{p['no']}",
                    use_container_width=True
                ):

                    st.session_state.view_post = p["no"]

                    st.rerun()

                if col3.button(
                    "🗑️",
                    key=f"del_{p['no']}",
                    use_container_width=True
                ):

                    st.session_state.posts = [

                        item for item in st.session_state.posts

                        if item["no"] != p["no"]

                    ]

                    save_json("data.json", st.session_state.posts)

                    st.rerun()
