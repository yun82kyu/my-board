import streamlit as st

def delete_category_logic(target, categories, cat_sha, save_json_func):
    """버튼 클릭 시 실행될 실제 로직 (on_click 콜백)"""
    if target and len(categories) > 1:
        categories.remove(target)
        save_json_func("categories.json", categories, cat_sha)
        # 현재 선택된 카테고리가 삭제 대상이면 첫 번째로 변경
        if st.session_state.get("current_cat") == target:
            st.session_state.current_cat = categories[0]
        st.toast(f"'{target}' 분류가 삭제되었습니다.")
    else:
        st.error("삭제할 수 없습니다.")

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # --- [1] 추가 섹션 ---
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_cat = st.text_input("새 분류 이름", key="input_new_cat_unique")
        if st.button("분류 추가 실행", key="btn_add_cat_unique", use_container_width=True):
            if new_cat and new_cat not in categories:
                categories.append(new_cat)
                save_json_func("categories.json", categories, cat_sha)
                st.rerun()

    st.write("")

    # --- [2] 삭제 섹션 (에러 발생 지점 해결) ---
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        
        deletable_cats = [
            c for c in categories 
            if len([i for i in all_data if i.get('category') == c]) == 0
        ]
        
        if not deletable_cats:
            st.info("삭제 가능한 빈 분류가 없습니다.")
        else:
            target = st.selectbox("삭제할 분류 선택", deletable_cats, key="sel_del_unique", index=None)
            confirm = st.checkbox("정말로 삭제하시겠습니까?", key="chk_del_unique")
            
            # [핵심] on_click을 사용하여 버튼 생성과 실행 로직을 물리적으로 분리
            st.button(
                "🔥 선택 분류 삭제", 
                key="btn_final_del_unique", 
                type="danger", 
                use_container_width=True,
                disabled=not (target and confirm),
                on_click=delete_category_logic,
                args=(target, categories, cat_sha, save_json_func)
            )

    st.divider()
    if st.button("⬅️ 메인으로 돌아가기", key="btn_exit_manager_unique"):
        st.session_state.view_mode = "list"
        st.rerun()
