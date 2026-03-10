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

# --- 2. 좌측 사이드바 (조건부 삭제 로직) ---
with st.sidebar:
    st.subheader("📁 대분류")
    
    # 분류 추가
    with st.popover("➕ 분류 추가", use_container_width=True):
        new_name = st.text_input("새 분류 명칭")
        if st.button("저장", key="add_cat_btn"):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json("categories.json", categories, cat_sha)
                st.rerun()

    st.divider()

    for idx, cat in enumerate(categories):
        # 글이 하나라도 있는지 확인
        post_count = len([i for i in all_data if i.get('category') == cat])
        
        # 글이 있으면 삭제 버튼 공간을 비우고(columns 비율 조정), 없으면 삭제 버튼 표시
        if post_count > 0:
            # 글이 있는 카테고리는 이름만 표시 (삭제 불가)
            if st.button(f"{cat} ({post_count})", key=f"cat_sel_{idx}", use_container_width=True, 
                         type="primary" if st.session_state.current_cat == cat else "secondary"):
                st.session_state.current_cat = cat
                st.query_params.clear()
                st.rerun()
        else:
            # 글이 없는 카테고리만 삭제 버튼(🗑️) 노출
            side_c1, side_c2 = st.columns([4, 1.2])
            if side_c1.button(cat, key=f"cat_sel_{idx}", use_container_width=True, 
                             type="primary" if st.session_state.current_cat == cat else "secondary"):
                st.session_state.current_cat = cat
                st.query_params.clear()
                st.rerun()
            
            if side_c2.button("🗑️", key=f"direct_del_{idx}", help="내용이 없어 즉시 삭제 가능"):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("최소 1개 필요")

# --- 3. 메인 화면 ---
params = st.query_params
current_view = params.get("view", "list")
selected_no = params.get("no", None)

# 상세 페이지
if current_view == "detail" and selected_no:
    post = next((i for i in all_data if str(i['no']) == str(selected_no)), None)
    if post:
        if st.button("⬅️ 목록"): st.query_params.clear(); st.rerun()
        st.divider()
        st.subheader(post['title'])
        st.info(post['content'])
    st.stop()

# 목록 페이지
st.title(f"👤 {st.session_state.current_cat}")
filtered_data = [i for i in all_data if i.get('category') == st.session_state.current_cat]

search_c, write_c = st.columns([5, 1.2])
search_q = search_c.text_input("", placeholder="🔍 제목 검색...", label_visibility="collapsed")

if write_c.button("📝 행 추가", use_container_width=True):
    st.session_state.show_main_write = not st.session_state.get("show_main_write", False)

if st.session_state.get("show_main_write", False):
    with st.form("main_write_form_stable", clear_on_submit=True):
        nt = st.text_input("제목")
        nc = st.text_area("내용")
        if st.form_submit_button("저장"):
            if nt and nc:
                n_no = max([int(i['no']) for i in all_data]) + 1 if all_data else 1
                all_data.insert(0, {"no": n_no, "title": nt, "name": "관리자", "content": nc, "category": st.session_state.current_cat})
                save_json("data.json", all_data, data_sha)
                st.session_state.show_main_write = False
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
