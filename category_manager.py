import streamlit as st

def delete_category_callback(cat, categories, cat_sha, save_json_func):
    """삭제 로직을 버튼 렌더링과 분리하여 실행하는 콜백 함수"""
    if len(categories) > 1:
        categories.remove(cat)
        save_json_func("categories.json", categories, cat_sha)
        # 삭제된 카테고리가 현재 선택된 것이라면 첫 번째로 변경
        if st.session_state.current_cat == cat:
            st.session_state.current_cat = categories[0]
        st.toast(f"'{cat}' 분류가 삭제되었습니다.")
    else:
        st.error("최소 한 개의 분류는 남겨두어야 합니다.")

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # 1. 신규 분류 추가 (Form 활용)
    with st.form("add_cat_form_fixed", clear_on_submit=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("분류 명칭", placeholder="새 이름을 입력하세요")
        if st.form_submit_button("추가하기", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json_func("categories.json", categories, cat_sha)
                st.rerun()

    st.write("")
    st.subheader("📋 분류 목록")

    # 헤더
    h1, h2, h3 = st.columns([3, 1, 1])
    h1.write("**분류명**"); h2.write("**글 개수**"); h3.write("**관리**")
    st.divider()

    # 2. 삭제 관리 리스트
    for idx, cat in enumerate(categories):
        r1, r2, r3 = st.columns([3, 1, 1])
        r1.write(f"**{cat}**")
        
        post_count = len([i for i in all_data if i.get('category') == cat])
        r2.write(f"{post_count} 개")
        
        if post_count == 0:
            # [핵심] on_click 콜백을 사용하여 버튼 클릭 시 로직을 격리 실행
            r3.button(
                "삭제", 
                key=f"final_del_btn_{cat}_{idx}", 
                type="danger", 
                use_container_width=True,
                on_click=delete_category_callback,
                args=(cat, categories, cat_sha, save_json_func)
            )
        else:
            r3.button("잠김", key=f"lock_btn_{idx}", disabled=True, use_container_width=True)

    st.write("")
    if st.button("← 메인으로 돌아가기", key="exit_manage_final"):
        st.session_state.view_mode = "list"
        st.rerun()
