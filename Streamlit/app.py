import streamlit as st
import os
from auth import register_user, login_user
import sqlite3
import base64

# Файл хадгалах хавтас үүсгэх
UPLOAD_FOLDER = "uploaded_files"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Page тохиргоо (Wide layout, icon)
st.set_page_config(page_title="DMS System", page_icon="📁", layout="wide")

# ==========================================
# 🎨 ЗАГВАР САЙЖРУУЛАХ CUSTOM CSS (ЗАСВАР ОРСОН)
# ==========================================
st.markdown("""
    <style>
        /* Үндсэн дэвсгэр өнгө */
        .stApp { background-color: #f4f7f6; }
        
        /* Хажуугийн цэсний дэвсгэр */
        [data-testid="stSidebar"] { 
            background-color: #1e293b; 
            border-right: 1px solid #334155; 
        }
        
        /* --- ХАЖУУГИЙН ЦЭСНИЙ БИЧГҮҮДИЙГ ЦАГААН БОЛГОХ --- */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label { 
            color: #f8fafc !important; 
        }
        
        /* ҮНДСЭН ЦЭС гэсэн гарчгийг арай бүдэг саарал болгох */
        [data-testid="stSidebar"] .stRadio > label p {
            color: #94a3b8 !important; 
            font-size: 0.9em;
        }
        
        /* Радио товчны Hover эффект */
        [data-testid="stSidebar"] div[role="radiogroup"] > label { 
            padding: 10px; 
            border-radius: 5px; 
            transition: 0.3s; 
            cursor: pointer; 
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { 
            background-color: #334155 !important; 
        }

        /* --- СИСТЕМЭЭС ГАРАХ ТОВЧИЙГ УЛААН БОЛГОХ --- */
        [data-testid="stSidebar"] .stButton > button {
            background-color: #ef4444 !important;
            color: white !important;
            border: none !important;
        }
        [data-testid="stSidebar"] .stButton > button p {
            color: white !important;
            font-weight: bold;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #dc2626 !important;
        }

        /* Баримтын картын мэдээлэл */
        .doc-meta {
            background-color: #e0f2fe; padding: 10px 15px; border-radius: 8px;
            color: #0369a1; font-size: 0.9em; margin-top: 5px; margin-bottom: 15px;
            border-left: 4px solid #0284c7;
        }
        h1, h2, h3 { color: #0f172a; }
        .doc-desc { color: #475569; font-size: 0.95em; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Session state-үүд
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
# Чатын түүхийг хадгалах
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# --- ФАЙЛЫГ ШУУД ВЭБ ДЭЭР ХАРАХ (VIEWER DIALOG) ---
@st.dialog("👀 Баримт бичиг үзэх", width="large")
def view_document_dialog(doc_title, file_path, file_type):
    st.markdown(f"<h3 style='color:#0284c7;'>📑 {doc_title}</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='doc-meta'>📂 Файлын төрөл: <b>{file_type}</b></div>", unsafe_allow_html=True)
    
    if os.path.exists(file_path):
        if "pdf" in file_type.lower():
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px" type="application/pdf" style="border-radius: 10px; border: 1px solid #ccc;"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        elif any(img_type in file_type.lower() for img_type in ["image", "png", "jpg", "jpeg"]):
            st.image(file_path, use_column_width=True, clamp=True)
        elif "text" in file_type.lower():
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
            st.text_area("Агуулга:", text_content, height=400)
        else:
            st.info("Энэ төрлийн файлыг шууд урьдчилан харах боломжгүй байна. Татаж авч үзнэ үү.")
    else:
        st.error("Файл сервер дээр олдсонгүй.")

# --- БАРИМТЫГ ЗАСАХ БОЛОН ФАЙЛЫГ НЬ СОЛИХ ПОПАП ЦОНХ ---
@st.dialog("✏️ Баримтын мэдээлэл засах")
def edit_document_dialog(doc_id, current_title, current_desc, current_author, current_file_path):
    with st.form(key=f"modal_edit_form_{doc_id}"):
        st.markdown("<h4 style='color:#333;'>Мэдээлэл шинэчлэх</h4>", unsafe_allow_html=True)
        new_title = st.text_input("Гарчиг", value=current_title)
        new_desc = st.text_area("Тайлбар", value=current_desc if current_desc else "")
        new_author = st.text_input("Зохиогч", value=current_author if current_author else "")
        
        st.markdown(f"<div class='doc-meta'>Одоогийн файл: <b>{os.path.basename(current_file_path)}</b></div>", unsafe_allow_html=True)
        # Хуучин: type=["pdf", "docx", "txt", "png", "jpg"]
        uploaded_file = st.file_uploader("Файлаа чирж оруулах эсвэл сонгох", type=["pdf", "doc", "docx", "txt", "png", "jpg"])
        
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            update_btn = st.form_submit_button("💾 Хадгалах", type="primary")
        with col_submit2:
            cancel_btn = st.form_submit_button("❌ Болих")
            
        if update_btn:
            conn = sqlite3.connect('dms_system.db')
            cursor = conn.cursor()
            final_file_path = current_file_path
            final_file_type = None
            
            if uploaded_file is not None:
                if os.path.exists(current_file_path):
                    os.remove(current_file_path)
                final_file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
                with open(final_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                final_file_type = uploaded_file.type
                
                cursor.execute('''UPDATE documents SET title = ?, description = ?, source_author = ?, file_path = ?, file_type = ? WHERE id = ?''', (new_title, new_desc, new_author, final_file_path, final_file_type, doc_id))
            else:
                cursor.execute('''UPDATE documents SET title = ?, description = ?, source_author = ? WHERE id = ?''', (new_title, new_desc, new_author, doc_id))
                
            conn.commit()
            conn.close()
            st.success("Баримт амжилттай шинэчлэгдлээ!")
            st.rerun()
            
        if cancel_btn:
            st.rerun()

# ==========================================
# 1. ХЭРЭВ НЭВТРЭЭСЭН БАЙВАЛ
# ==========================================
if st.session_state.logged_in:
    
    # --- ХАЖУУГИЙН ЦЭС (SIDEBAR) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135679.png", width=100)
        st.markdown(f"<h3 style='color: white; margin-bottom: 0;'>{st.session_state.username}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; margin-top: 0;'>Эрх: <b>{st.session_state.role}</b></p>", unsafe_allow_html=True)
        st.divider()
        
        # Үндсэн цэсний сонголт
        page_selection = st.radio("ҮНДСЭН ЦЭС", ["📁 Баримт бичиг", "💬 Шинэ чат (AI)"])
        
        st.divider()
        if st.button("🚪 Системээс гарах", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()

    # ==========================================
    # ХУУДАС 1: БАРИМТ БИЧИГ (DOCUMENTS)
    # ==========================================
    if page_selection == "📁 Баримт бичиг":
        st.markdown("<h1>📁 Баримт Бичиг Удирдлагын Систем</h1>", unsafe_allow_html=True)
        
        conn = sqlite3.connect('dms_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.close()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📄 Нийт Баримт", f"{total_docs} ш")
        if st.session_state.role == "Admin":
            m2.metric("👥 Нийт Хэрэглэгч", f"{total_users} хүн")
        st.divider()

        # --- АДМИН ХЭРЭГЛЭГЧ ---
        if st.session_state.role == "Admin":
            admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📄 Баримтын жагсаалт", "📤 Шинэ файл оруулах", "👥 Хэрэглэгчид"])

            with admin_tab1:
                search_query = st.text_input("🔍 Баримт хайх (Гарчиг эсвэл зохиогчоор)...", placeholder="Энд бичиж хайна уу...")
                conn = sqlite3.connect('dms_system.db')
                cursor = conn.cursor()
                if search_query:
                    cursor.execute('''SELECT id, title, description, file_path, file_type, source_author, upload_date FROM documents WHERE title LIKE ? OR source_author LIKE ? ORDER BY id DESC''', (f'%{search_query}%', f'%{search_query}%'))
                else:
                    cursor.execute('''SELECT id, title, description, file_path, file_type, source_author, upload_date FROM documents ORDER BY id DESC''')
                documents = cursor.fetchall()
                conn.close()

                if documents:
                    for doc in documents:
                        doc_id = doc[0]
                        with st.container(border=True):
                            st.markdown(f"<h3 style='color:#0f172a; margin-bottom:5px;'>📑 {doc[1]}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<div class='doc-desc'>{doc[2] if doc[2] else 'Тайлбар оруулаагүй байна...'}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='doc-meta'>👤 <b>Зохиогч:</b> {doc[5]} &nbsp;|&nbsp; 📅 <b>Огноо:</b> {doc[6]} &nbsp;|&nbsp; 📂 <b>Төрөл:</b> {doc[4]}</div>", unsafe_allow_html=True)
                            
                            col_v, col_dl, col_del, col_edit, col_space = st.columns([1, 1.2, 1, 1, 6])
                            with col_v:
                                if st.button("👀 Үзэх", key=f"view_{doc_id}", use_container_width=True):
                                    view_document_dialog(doc[1], doc[3], doc[4])
                            with col_dl:
                                if os.path.exists(doc[3]):
                                    with st.popover("📥 Татах", use_container_width=True):
                                        st.write("Татах форматаа сонгоно уу:")
                                        with open(doc[3], "rb") as file:
                                            file_data = file.read()
                                        base_name = os.path.splitext(os.path.basename(doc[3]))[0]
                                        st.download_button(label="📄 PDF файлаар", data=file_data, file_name=f"{base_name}.pdf", mime="application/pdf", key=f"dl_pdf_{doc_id}", use_container_width=True)
                                        st.download_button(label="📝 Word файлаар", data=file_data, file_name=f"{base_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_word_{doc_id}", use_container_width=True)
                            with col_edit:
                                if st.button("✏️ Засах", key=f"edit_btn_{doc_id}", use_container_width=True):
                                    edit_document_dialog(doc_id, doc[1], doc[2], doc[5], doc[3])
                            with col_del:
                                if st.button("🗑️ Устгах", key=f"del_{doc_id}", type="primary", use_container_width=True):
                                    conn = sqlite3.connect('dms_system.db')
                                    cursor = conn.cursor()
                                    if os.path.exists(doc[3]):
                                        os.remove(doc[3])
                                    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                else:
                    st.info("Системд одоогоор баримт бүртгэгдээгүй байна.")

            with admin_tab2:
                st.markdown("<h3 style='color:#0284c7;'>📤 Шинэ баримт байршуулах</h3>", unsafe_allow_html=True)
                with st.form("admin_upload_form", clear_on_submit=True):
                    doc_title = st.text_input("Баримтын гарчиг*")
                    doc_desc = st.text_area("Тайлбар")
                    doc_author = st.text_input("Зохиогч / Эх сурвалж")
                    uploaded_file = st.file_uploader("Файлаа чирж оруулах эсвэл сонгох", type=["pdf", "doc", "docx", "txt", "png", "jpg"])
                    
                    submit_button = st.form_submit_button("Файлыг хадгалах", type="primary")
                    
                    if submit_button:
                        if doc_title and uploaded_file:
                            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            conn = sqlite3.connect('dms_system.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.username,))
                            user_id = cursor.fetchone()[0]

                            cursor.execute('''INSERT INTO documents (title, description, file_path, file_type, source_author, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)''', (doc_title, doc_desc, file_path, uploaded_file.type, doc_author, user_id))
                            conn.commit()
                            conn.close()
                            st.success("Файл амжилттай байршлаа!")
                            st.rerun()
                        else:
                            st.warning("Гарчиг болон файлыг заавал оруулна уу!")

            with admin_tab3:
                st.markdown("### 👥 Системийн хэрэглэгчид")
                conn = sqlite3.connect('dms_system.db')
                cursor = conn.cursor()
                cursor.execute('''SELECT users.username, roles.role_name, users.status, users.created_at FROM users JOIN roles ON users.role_id = roles.id''')
                users_list = cursor.fetchall()
                conn.close()

                for u in users_list:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"👤 **{u[0]}** <br> <span style='font-size:0.8em; color:gray;'>Бүртгүүлсэн: {u[3]}</span>", unsafe_allow_html=True)
                        c2.markdown(f"🛡️ **Эрх:** {u[1]}")
                        c3.markdown(f"🟢 **Төлөв:** {u[2]}")

        # --- ЭНГИЙН ХЭРЭГЛЭГЧ ---
        else:
            search_query = st.text_input("🔍 Баримт хайх (Гарчиг эсвэл зохиогчоор)...", placeholder="Хайх үгээ бичнэ үү...")
            conn = sqlite3.connect('dms_system.db')
            cursor = conn.cursor()
            if search_query:
                cursor.execute('''SELECT id, title, description, file_path, file_type, source_author, upload_date FROM documents WHERE title LIKE ? OR source_author LIKE ? ORDER BY id DESC''', (f'%{search_query}%', f'%{search_query}%'))
            else:
                cursor.execute('''SELECT id, title, description, file_path, file_type, source_author, upload_date FROM documents ORDER BY id DESC''')
            documents = cursor.fetchall()
            conn.close()

            if documents:
                for doc in documents:
                    doc_id = doc[0]
                    with st.container(border=True):
                        st.markdown(f"<h3 style='color:#0f172a; margin-bottom:5px;'>📑 {doc[1]}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<div class='doc-desc'>{doc[2] if doc[2] else 'Тайлбар оруулаагүй байна...'}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='doc-meta'>👤 <b>Зохиогч:</b> {doc[4]} &nbsp;|&nbsp; 📅 <b>Огноо:</b> {doc[5]} &nbsp;|&nbsp; 📂 <b>Төрөл:</b> {doc[3]}</div>", unsafe_allow_html=True)
                        
                        col_uv, col_udl, col_uspace = st.columns([1, 1.2, 8])
                        with col_uv:
                            if st.button("👀 Үзэх", key=f"user_view_{doc_id}", use_container_width=True):
                                view_document_dialog(doc[0], doc[2], doc[3])
                        with col_udl:
                            if os.path.exists(doc[3]):
                                with st.popover("📥 Татах", use_container_width=True):
                                    st.write("Татах форматаа сонгоно уу:")
                                    with open(doc[3], "rb") as file:
                                        file_data = file.read()
                                    base_name = os.path.splitext(os.path.basename(doc[3]))[0]
                                    st.download_button(label="📄 PDF файлаар", data=file_data, file_name=f"{base_name}.pdf", mime="application/pdf", key=f"udl_pdf_{doc_id}", use_container_width=True)
                                    st.download_button(label="📝 Word файлаар", data=file_data, file_name=f"{base_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"udl_word_{doc_id}", use_container_width=True)
            else:
                st.info("Системд одоогоор баримт бүртгэгдээгүй байна.")

    # ==========================================
    # ХУУДАС 2: ШИНЭ ЧАТ (AI CHAT)
    # ==========================================
    elif page_selection == "💬 Шинэ чат (AI)":
        st.markdown("<h1>💬 Баримт бичигтэй харилцах AI туслах</h1>", unsafe_allow_html=True)
        st.caption("Та системд хадгалагдсан байгаа баримтуудын хүрээнд асуулт асуух боломжтой.")
        st.divider()

        # Өмнөх чатын түүхийг харуулах
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Шинэ мессеж оруулах хэсэг
        prompt = st.chat_input("Баримтаас хайх зүйлээ энд бичнэ үү...")
        
        if prompt:
            # Хэрэглэгчийн бичсэнийг дэлгэцэнд гаргах
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # AI-ийн хариулт
            with st.chat_message("assistant"):
                response = f"Уучлаарай, би таны '{prompt}' гэсэн асуултыг хүлээж авлаа. Одоогоор AI загвар (LLM) бүрэн холбогдоогүй байгаа тул баримтаас хайлт хийх боломжгүй байна. Дараагийн шатанд LangChain эсвэл OpenAI холбогдоход би шууд баримт дотроос хариулах болно!"
                st.write(response)
            
            st.session_state.chat_messages.append({"role": "assistant", "content": response})

# ==========================================
# 2. ХЭРЭВ НЭВТРЭЭГҮЙ БАЙВАЛ (LOGIN / REGISTER)
# ==========================================
else:
    st.markdown("<h1 style='text-align: center; color: #1e293b; margin-bottom: 30px;'>📁 Баримт Бичиг Удирдлагын Систем</h1>", unsafe_allow_html=True)
    
    col_empty1, col_center, col_empty2 = st.columns([1, 2, 1])
    
    with col_center:
        tab_login, tab_register = st.tabs(["🔐 Нэвтрэх", "📝 Бүртгүүлэх"])

        with tab_login:
            st.markdown("<h3 style='color:#0284c7;'>Системд нэвтрэх</h3>", unsafe_allow_html=True)
            login_user_input = st.text_input("Нэвтрэх нэр", key="login_user")
            login_password = st.text_input("Нууц үг", type="password", key="login_pass")
            
            if st.button("Нэвтрэх", type="primary", use_container_width=True):
                if login_user_input and login_password:
                    success, role, message = login_user(login_user_input, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = login_user_input
                        st.session_state.role = role
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Бүх талбарын бөглөнө үү!")

        with tab_register:
            st.markdown("<h3 style='color:#0284c7;'>Шинээр бүртгүүлэх</h3>", unsafe_allow_html=True)
            reg_username = st.text_input("Шинэ нэвтрэх нэр (Username)", key="reg_user")
            reg_password = st.text_input("Шинэ нууц үг (Password)", type="password", key="reg_pass")
            
            if st.button("Бүртгүүлэх", use_container_width=True):
                if reg_username and reg_password:
                    success, msg = register_user(reg_username, reg_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Бүх талбарыг бөглөнө үү!")