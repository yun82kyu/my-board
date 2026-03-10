import streamlit as st

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    st.info("내용이 있는 분류는 삭제할 수 없습니다.")
    
    # 1. 추가 섹션
    with st.form("add_category_form", clear_on_submit=True):
        st.subheader("➕ 신규 분류 추가")
        new_cat_input = st.text_input("분류 명칭", placeholder="새 분류 이름을 입력하세요")
        if st.form_submit_button("추가하기", use_container_width=True):
            if new_cat_input and new_cat_input not in categories:
                categories.append(new_cat_input)
                save_json_func("categories.json", categories, cat_sha)
                st.rerun()

    st.write("")

    # 2. 삭제 관리 섹션
    st.subheader("📋 분류 목록 및 삭제")
    h_col1, h_col2, h_col3 = st.columns([3, 1, 1])
    h_col1.write("**분류명**"); h_col2.write("**게시글**"); h_col3.write("**관리**")
    st.divider()

    for idx, cat in enumerate(categories):
        r1, r2, r3 = st.columns([3, 1, 1])
        r1.write(f"**{cat}**")
        
        post_count = len([i for i in all_data if i.get('category') == cat])
        r2.write(f"{post_count} 개")
        
        if post_count == 0:
            if r3.button("삭제", key=f"m_del_{idx}", type="danger", use_container_width=True):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json_func("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
        else:
            r3.button("잠김", key=f"m_lock_{idx}", disabled=True, use_container_width=True)

    if st.button("← 메인 목록으로", key="back_to_main"):
        st.session_state.view_mode = "list"
        st.rerun()
