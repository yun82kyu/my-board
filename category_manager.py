import streamlit as st

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # --- [1] 신규 분류 추가 섹션 ---
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", key="m_input_add_name")
        # 추가 버튼
        if st.button("분류 추가 실행", key="m_btn_add_exec", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json_func("categories.json", categories, cat_sha)
                st.rerun()
            elif new_name in categories:
                st.warning("이미 있는 이름입니다.")

    st.write("")

    # --- [2] 분류 삭제 섹션 ---
    # 삭제 실행 여부를 저장할 변수
    do_delete = False
    target_to_remove = None

    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        
        deletable_cats = [
            c for c in categories 
            if len([i for i in all_data if i.get('category') == c]) == 0
        ]
        
        if not deletable_cats:
            st.info("삭제 가능한 빈 분류가 없습니다.")
        else:
            target_to_remove = st.selectbox("삭제할 분류 선택", deletable_cats, key="m_select_del", index=None, placeholder="분류를 고르세요")
            confirm = st.checkbox("정말로 삭제하시겠습니까?", key="m_check_confirm")
            
            # 버튼 클릭 시 즉시 실행하지 않고 '신호(Signal)'만 보냄
            if st.button("🔥 선택 분류 삭제", key="m_btn_del_final", type="danger", use_container_width=True):
                if not target_to_remove:
                    st.error("분류를 선택해주세요.")
                elif not confirm:
                    st.warning("삭제 확인 체크박스에 체크해주세요.")
                else:
                    do_delete = True # 루프 밖에서 처리하기 위해 표시

    # 🌟 [중요] 모든 위젯 생성이 끝난 루프 밖에서 실제 데이터 처리를 진행
    if do_delete and target_to_remove:
        if len(categories) > 1:
            categories.remove(target_to_remove)
            save_json_func("categories.json", categories, cat_sha)
            # 현재 선택된 카테고리가 삭제된 경우 이동
            if st.session_state.current_cat == target_to_remove:
                st.session_state.current_cat = categories[0]
            st.rerun()
        else:
            st.error("최소 1개는 유지해야 합니다.")

    st.divider()
    if st.button("⬅️ 메인으로 돌아가기", key="m_btn_exit_manager"):
        st.session_state.view_mode = "list"
        st.rerun()
