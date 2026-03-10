import streamlit as st

# 부분 렌더링을 위해 fragment 데코레이터 사용
@st.fragment
def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # 1. 신규 분류 추가 (Form은 언제나 안전합니다)
    with st.form("add_cat_form", clear_on_submit=True):
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

    # 삭제 대상 추적
    for idx, cat in enumerate(categories):
        r1, r2, r3 = st.columns([3, 1, 1])
        r1.write(f"**{cat}**")
        
        post_count = len([i for i in all_data if i.get('category') == cat])
        r2.write(f"{post_count} 개")
        
        # 글이 0개인 경우에만 삭제 버튼 활성화
        if post_count == 0:
            # unique key를 보장하기 위해 카테고리 이름과 인덱스 조합
            if r3.button("삭제", key=f"del_final_{cat}_{idx}", type="danger", use_container_width=True):
                if len(categories) > 1:
                    categories.remove(cat)
                    save_json_func("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == cat:
                        st.session_state.current_cat = categories[0]
                    st.rerun()
                else:
                    st.error("최소 한 개의 분류는 남겨두어야 합니다.")
        else:
            r3.button("잠김", key=f"lock_{idx}", disabled=True, use_container_width=True)

    st.write("")
    if st.button("← 메인으로 돌아가기", key="exit_manage_mode"):
        st.session_state.view_mode = "list"
        st.rerun()
