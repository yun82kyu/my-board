import streamlit as st

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # --- SECTION 1: 대분류 추가 ---
    with st.form("add_category_form", clear_on_submit=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", placeholder="예: 자유게시판")
        if st.form_submit_button("추가하기", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json_func("categories.json", categories, cat_sha)
                st.success(f"'{new_name}' 추가 완료!")
                st.rerun()

    st.write("")

    # --- SECTION 2: 대분류 삭제 (에러 방지 핵심 로직) ---
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        
        # 삭제 가능한(글이 0개인) 카테고리만 추출
        deletable_cats = [
            cat for cat in categories 
            if len([i for i in all_data if i.get('category') == cat]) == 0
        ]
        
        if not deletable_cats:
            st.info("현재 삭제 가능한(비어 있는) 분류가 없습니다.")
        else:
            # 삭제할 대상을 하나 고르게 함 (버튼 여러 개를 안 만듦으로써 에러 차단)
            target_cat = st.selectbox("삭제할 분류를 선택하세요", deletable_cats, index=None, placeholder="분류 선택...")
            
            # 최종 확인 버튼 (루프 밖에서 단 하나만 존재)
            if st.button("선택한 분류 즉시 삭제", type="danger", use_container_width=True):
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

    st.write("")
    
    # --- SECTION 3: 현재 전체 목록 보기 (단순 텍스트 출력) ---
    st.subheader("📋 현재 대분류 현황")
    for cat in categories:
        count = len([i for i in all_data if i.get('category') == cat])
        st.write(f"- **{cat}** (게시글: {count}개)")

    if st.button("← 메인 게시판으로", key="back_to_main_page"):
        st.session_state.view_mode = "list"
        st.rerun()
