import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="거래처별 정책 조회 시스템", layout="wide")

# 데이터 저장을 위한 기본 파일 경로
DATA_DIR = "data"
EXCEL_DIR = os.path.join(DATA_DIR, "excels") # 엑셀 파일들을 따로 모아둘 폴더
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXCEL_DIR, exist_ok=True)

CLIENT_FILE = os.path.join(DATA_DIR, "clients.csv")
GROUP_FILE = os.path.join(DATA_DIR, "groups.csv")
HISTORY_FILE = os.path.join(DATA_DIR, "upload_history.csv") # 업로드 이력 관리 파일

# 초기 데이터 파일 생성 (처음 실행 시)
if not os.path.exists(CLIENT_FILE):
    pd.DataFrame(columns=["client_id", "password", "client_name", "group_name"]).to_csv(CLIENT_FILE, index=False)

if not os.path.exists(GROUP_FILE):
    pd.DataFrame(columns=["group_name"]).to_csv(GROUP_FILE, index=False)

if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=["group_name", "file_name", "stored_filename", "upload_time"]).to_csv(HISTORY_FILE, index=False)

# 데이터 로드/저장 함수들
def load_clients():
    return pd.read_csv(CLIENT_FILE, dtype=str)

def save_clients(df):
    df.to_csv(CLIENT_FILE, index=False)

def load_groups():
    df = pd.read_csv(GROUP_FILE)
    return df["group_name"].tolist() if not df.empty else []

def save_groups(groups):
    pd.DataFrame({"group_name": groups}).to_csv(GROUP_FILE, index=False)

def load_history():
    return pd.read_csv(HISTORY_FILE, dtype=str)

def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- [로그인 화면] ---
if not st.session_state.logged_in:
    st.title("🔒 거래처 정책 조회 시스템 로그인")
    
    login_type = st.radio("로그인 유형을 선택하세요", ["거래처 사용자", "관리자"])
    
    if login_type == "관리자":
        admin_id = st.text_input("관리자 아이디")
        admin_pw = st.text_input("관리자 비밀번호", type="password")
        if st.button("관리자 로그인"):
            if admin_id == "admin" and admin_pw == "1234":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.rerun()
            else:
                st.error("관리자 아이디 또는 비밀번호가 틀렸습니다.")
                
    else:
        client_id = st.text_input("거래처 아이디")
        client_pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            clients_df = load_clients()
            user = clients_df[(clients_df["client_id"] == client_id) & (clients_df["password"] == client_pw)]
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = "client"
                st.session_state.username = user.iloc[0]["client_name"]
                st.session_state.group_name = user.iloc[0]["group_name"]
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

# --- [로그인 이후 화면] ---
else:
    # 1. 관리자 모드
    if st.session_state.user_role == "admin":
        st.sidebar.title("🛠️ 관리자 메뉴")
        menu = st.sidebar.radio("이동", ["정책 그룹 및 엑셀 관리", "거래처 관리", "로그아웃"])
        
        if menu == "로그아웃":
            st.session_state.logged_in = False
            st.rerun()
            
        elif menu == "정책 그룹 및 엑셀 관리":
            st.title("📁 정책 그룹 및 엑셀 파일 관리")
            groups = load_groups()
            
            # 새 그룹 추가
            new_group = st.text_input("새로운 정책 그룹명 입력 (예: 정책A, 정책B 등)")
            if st.button("그룹 추가"):
                if new_group and new_group not in groups:
                    groups.append(new_group)
                    save_groups(groups)
                    st.success(f"'{new_group}' 그룹이 추가되었습니다!")
                    st.rerun()
                elif new_group in groups:
                    st.warning("이미 존재하는 그룹입니다.")
            
            st.write("---")
            st.subheader("그룹별 정책 엑셀 파일 업로드")
            if groups:
                selected_group = st.selectbox("파일을 업로드할 그룹 선택", groups)
                uploaded_file = st.file_uploader(f"[{selected_group}]에 적용할 엑셀 파일 업로드 (.xlsx)", type=["xlsx"])
                
                if uploaded_file is not None:
                    # 파일 고유 이름 생성 (중복 방지를 위해 시간 조합)
                    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    original_name = uploaded_file.name
                    stored_filename = f"{selected_group}_{now_str}_{original_name}"
                    file_path = os.path.join(EXCEL_DIR, stored_filename)
                    
                    # 파일 저장
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 이력 저장
                    history_df = load_history()
                    new_history = pd.DataFrame({
                        "group_name": [selected_group],
                        "file_name": [original_name],
                        "stored_filename": [stored_filename],
                        "upload_time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    })
                    history_df = pd.concat([history_df, new_history], ignore_index=True)
                    save_history(history_df)
                    
                    st.success(f"[{selected_group}] 그룹에 '{original_name}' 파일이 성공적으로 업로드되었습니다!")
                
                st.write("---")
                st.subheader(f"[{selected_group}] 그룹의 업로드 파일 이력")
                history_df = load_history()
                group_history = history_df[history_df["group_name"] == selected_group]
                
                if not group_history.empty:
                    # 최신순 정렬
                    group_history = group_history.iloc[::-1]
                    for idx, row in group_history.iterrows():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.text(f"파일: {row['file_name']}")
                        with col2:
                            st.text(f"일시: {row['upload_time']}")
                        with col3:
                            target_path = os.path.join(EXCEL_DIR, row['stored_filename'])
                            if os.path.exists(target_path):
                                with open(target_path, "rb") as f:
                                    st.download_button(
                                        label="다운로드",
                                        data=f,
                                        file_name=row['file_name'],
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_{row['stored_filename']}"
                                    )
                else:
                    st.info("아직 업로드된 파일 이력이 없습니다.")
            else:
                st.info("등록된 정책 그룹이 없습니다. 먼저 그룹을 추가해주세요.")

        elif menu == "거래처 관리":
            st.title("👥 거래처 등록 및 그룹 매칭 관리")
            groups = load_groups()
            clients_df = load_clients()
            
            with st.form("client_form"):
                st.subheader("신규 거래처 등록")
                c_id = st.text_input("거래처 아이디")
                c_pw = st.text_input("비밀번호")
                c_name = st.text_input("거래처 상호명")
                c_group = st.selectbox("소속 정책 그룹", groups if groups else ["그룹 없음"])
                
                submitted = st.form_submit_button("거래처 등록")
                if submitted:
                    if c_id and c_pw and c_name and c_group != "그룹 없음":
                        if c_id in clients_df["client_id"].values:
                            st.error("이미 존재하는 거래처 아이디입니다.")
                        else:
                            new_row = pd.DataFrame({"client_id": [c_id], "password": [c_pw], "client_name": [c_name], "group_name": [c_group]})
                            clients_df = pd.concat([clients_df, new_row], ignore_index=True)
                            save_clients(clients_df)
                            st.success(f"[{c_name}] 거래처가 등록되었습니다!")
                            st.rerun()
                    else:
                        st.warning("모든 정보를 올바르게 입력해주세요.")
            
            st.write("---")
            st.subheader("등록된 거래처 목록")
            if not clients_df.empty:
                st.dataframe(clients_df[["client_id", "client_name", "group_name"]], use_container_width=True)
                
                del_id = st.selectbox("삭제할 거래처 아이디 선택", clients_df["client_id"].tolist())
                if st.button("선택한 거래처 삭제"):
                    clients_df = clients_df[clients_df["client_id"] != del_id]
                    save_clients(clients_df)
                    st.success("삭제되었습니다.")
                    st.rerun()
            else:
                st.info("등록된 거래처가 없습니다.")

    # 2. 거래처 사용자 모드
    elif st.session_state.user_role == "client":
        st.title(f"환영합니다, {st.session_state.username}님!")
        st.write(f"현재 배정된 정책 그룹: **{st.session_state.group_name}**")
        
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
            
        st.write("---")
        st.subheader("📋 우리 회사 적용 정책 파일 목록")
        st.write("가장 최근에 업로드된 최신 정책 파일을 다운로드하여 확인하세요. 과거에 업로드된 파일들도 아래에서 다운로드 가능합니다.")
        
        history_df = load_history()
        group_history = history_df[history_df["group_name"] == st.session_state.group_name]
        
        if not group_history.empty:
            # 최신순 정렬
            group_history = group_history.iloc[::-1]
            for idx, row in group_history.iterrows():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(f"파일: {row['file_name']}")
                with col2:
                    st.text(f"등록일시: {row['upload_time']}")
                with col3:
                    target_path = os.path.join(EXCEL_DIR, row['stored_filename'])
                    if os.path.exists(target_path):
                        with open(target_path, "rb") as f:
                            st.download_button(
                                label="다운로드",
                                data=f,
                                file_name=row['file_name'],
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"client_dl_{row['stored_filename']}"
                            )
        else:
            st.warning("현재 해당 그룹에 등록된 정책 파일이 없습니다. 관리자에게 문의해주세요.")