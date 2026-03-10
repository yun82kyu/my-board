import streamlit as st

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # --- [추가 섹션] ---
    with st.form("form_add_category_unique", clear_on_submit=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", placeholder="예: 자유게시판", key="input_new_cat_name")
        submit_add = st.form_submit_button("추가하기", use_container_width=True)
        
        if submit_add:
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json_func("categories.json", categories, cat_sha)
                st.success(f"'{new_name}' 추가 완료!")
                st.rerun()

    st.write("---")

    # --- [삭제 섹션] ---
    st.subheader("🗑️ 분류 삭제")
    
    # 삭제 가능한(글이 0개인) 카테고리 추출
    deletable_cats = [
        cat for cat in categories 
        if len([i for i in all_data if i.get('category') == cat]) == 0
    ]
    
    if not deletable_cats:
        st.info("현재 삭제 가능한(비어 있는) 분류가 없습니다.")
    else:
        # selectbox에 고유 key 부여
        target_cat = st.selectbox(
            "삭제할 분류를 선택하세요", 
            deletable_cats, 
            index=None, 
            placeholder="분류 선택...",
            key="selectbox_delete_target"
        )
        
        # 삭제 버튼에 절대 중복되지 않는 고유 key 부여
        if st.button("선택한 분류 즉시 삭제", type="danger", use_container_width=True, key="btn_final_delete_action"):
            if target_cat and len(categories) > 1:
                categories.remove(target_cat)
                save_json_func("categories.json", categories, cat_sha)
                if st.session_state.current_cat == target_cat:
                    st.session_state.current_cat = categories[0]
                st.rerun()
            elif not target_cat:
                st.warning("삭제할 대상을 먼저 선택해주세요.")
            else:
                st.error("최소 한 개의 분류는 남겨두어야 합니다.")

    st.write("---")
    
    # --- [목록 확인] ---
    st.subheader("📋 현재 대분류 현황")
    for idx, cat in enumerate(categories):
        count = len([i for i in all_data if i.get('category') == cat])
        st.write(f"{idx+1}. **{cat}** (게시글: {count}개)")

    # 돌아가기 버튼에도 고유 key 부여
    if st.button("← 메인 게시판으로", key="btn_back_to_main_dashboard"):
        st.session_state.view_mode = "list"
        st.rerun()
