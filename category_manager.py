import streamlit as st

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # --- 1. 신규 분류 추가 (Form은 독립된 공간이라 안전합니다) ---
    with st.form("form_add_new_cat", clear_on_submit=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", key="input_add_name")
        if st.form_submit_button("추가하기", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json_func("categories.json", categories, cat_sha)
                st.rerun()

    st.write("---")

    # --- 2. 분류 삭제 (체크박스 방식 - 가장 안전함) ---
    st.subheader("🗑️ 분류 삭제")
    st.caption("글이 0개인 분류만 목록에 나타납니다.")

    # 삭제 가능한 분류 찾기
    deletable_cats = [
        cat for cat in categories 
        if len([i for i in all_data if i.get('category') == cat]) == 0
    ]

    if not deletable_cats:
        st.info("삭제 가능한 빈 분류가 없습니다.")
    else:
        # 폼으로 감싸서 버튼 클릭 시에만 삭제가 일어나도록 격리
        with st.form("delete_management_form"):
            target_to_del = st.selectbox("삭제할 분류 선택", deletable_cats, key="select_del_target")
            confirm_check = st.checkbox("위 분류를 영구 삭제하는 것에 동의합니다.", key="check_del_confirm")
            
            submit_del = st.form_submit_button("🔥 선택 분류 삭제 실행", type="danger", use_container_width=True)
            
            if submit_del:
                if not confirm_check:
                    st.warning("동의 체크박스를 선택해주세요.")
                elif target_to_del and len(categories) > 1:
                    categories.remove(target_to_del)
                    save_json_func("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == target_to_del:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("삭제할 수 없습니다 (최소 1개 유지 필요).")

    st.write("---")
    if st.button("← 메인 게시판으로 돌아가기", key="btn_exit_manager"):
        st.session_state.view_mode = "list"
        st.rerun()
