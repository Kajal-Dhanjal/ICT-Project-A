# 🗒️ Team Notes

Use this document to track important technical setup steps and security modules across the project.

---

## 🗄️ Database
> All care plan entries, vitals, medications, and file attachments written by nurses are stored in the database.  
Admins and nurses manage resident creation and assignments via the web interface.

---

## 🔐 Encryption


---

## 🔑 MFA


---

## 🔏 RBAC
> Role-Based Access Control is enforced:
- **Admins** can create users/residents and assign access, but **cannot see medical records**
- **Nurses** have read/write access only to residents assigned with write permission
- **Carers** have **read-only** access to residents assigned to them

---

## 🌐 Web Perimeter Security (HTTPS + Ngrok)

### To run HTTPS locally using Flask + Ngrok:

#### ▶️ On VS Code Terminal:
python app.py

**On Git Bash:**
cd tools
./ngrok.exe http https://localhost:5000

Copy the link and paste it in your browser. 

