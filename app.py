import streamlit as st
import json
from github import Github

# --- 1. 보안 및 데이터 로드 ---
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

# 데이터 로드
categories, cat_sha = load_json("categories.json")
all_data, data_sha = load_json("data.json")

if "current_cat" not in st.session_state:
    st.session_state.current_cat = categories[0] if categories else "기본분류"

# --- 2. 좌측 사이드바 (화살표 없는 삭제 로직) ---
with st.sidebar:
    st.subheader("📁 대분류")
    
    # 분류 추가 (여기는 팝업 유지 혹은 버튼으로 변경 가능)
    with st.popover("➕ 분류 추가", use_container_width=True):
        new_name = st.text_input("새 분류 명칭")
        if st.button("저장", key="add_cat_final"):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json("categories.json", categories, cat_sha)
                st.rerun()

    st.write("") 

    for idx, cat in enumerate(categories):
        side_c1, side_c2 = st.columns([4, 1.2])
        
        is_sel = (st.session_state.current_cat == cat)
        if side_c1.button(cat, key=f"cat_sel_{idx}", use_container_width=True, type="primary" if is_sel else "secondary"):
            st.session_state.current_cat = cat
            st.query_params.clear()
            st.rerun()
            
        # 삭제 버튼 (st.popover 대신 st.button 사용으로 화살표 제거)
        if side_c2.button("🗑️", key=f"del_btn_{idx}"):
            # 삭제 모드 세션 전환
            st.session_state[f"delete_mode_{idx}"] = not st.session_state.get(f"delete_mode_{idx}", False)

        # 삭제 버튼을 눌렀을 때만 나타나는 확인창 (조건부 렌더링)
        if st.session_state.get(f"delete_mode_{idx}", False):
            post_count = len([i for i in all_data if i.get('category') == cat])
            with st.container(border=True):
                if post_count > 0:
                    st.caption(f"글 {post_count}개 존재")
                st.write("삭제?")
                col_y, col_n = st.columns(2)
                if col_y.button("OK", key=f"yes_{idx}", type="danger"):
                    if len(categories) > 1:
                        categories.remove(cat)
                        save_json("categories.json", categories, cat_sha)
                        if st.session_state.current_cat == cat:
                            st.session_state.current_cat = categories[0]
                        st.session_state[f"delete_mode_{idx}"] = False
                        st.rerun()
                if col_n.button("NO", key=f"no_{idx}"):
                    st.session_state[f"delete_mode_{idx}"] = False
                    st.rerun()

# --- 3. 메인 화면 목록 (화살표 없는 행 추가) ---
st.title(f"👤 {st.session_state.current_cat}")
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", label_visibility="collapsed")

# 행 추가 버튼 (여기도 화살표가 싫다면 팝업 대신 버튼으로 변경 가능)
if write_c.button("📝 행 추가", use_container_width=True):
    st.session_state.show_write = not st.session_state.get("show_write", False)

if st.session_state.get("show_write", False):
    with st.form("main_write_form", clear_on_submit=True):
        st.write(f"**[{st.session_state.current_cat}]** 신규 작성")
        nt = st.text_input("제목")
        nc = st.text_area("내용")
        c1, c2 = st.columns([1, 5])
        if c1.form_submit_button("저장"):
            if nt and nc:
                n_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {"no": n_no, "title": nt, "name": "관리자", "content": nc, "category": st.session_state.current_cat})
                save_json("data.json", all_data, data_sha)
                st.session_state.show_write = False
                st.rerun()
        if c2.button("닫기"):
            st.session_state.show_write = False
            st.rerun()

st.write("")
h1, h2, h3, h4 = st.columns([0.6, 6, 1.5, 0.8])
h1.write("**No**"); h2.write("**Title**"); h3.write("**Name**"); h4.write("**Del**")
st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

for item in filtered_data:
    if search_q and search_q.lower() not in item['title'].lower():
        continue
    c1, c2, c3, c4 = st.columns([0.6, 6, 1.5, 0.8])
    c1.write(item['no'])
    if c2.button(item['title'], key=f"post_{item['no']}", use_container_width=True):
        st.query_params.update(view="detail", no=item['no'])
        st.rerun()
    c3.write(item.get('name', '관리자'))
    if c4.button("🗑️", key=f"row_del_{item['no']}"):
        all_data = [i for i in all_data if i['no'] != item['no']]
        save_json("data.json", all_data, data_sha)
        st.rerun()
