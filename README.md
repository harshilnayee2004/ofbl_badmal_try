# MIPL Ordnance AI Quality Inspection System

## Quick Start (Next Time You Run)

### Method 1: One-Click Startup (Recommended)
Simply double-click:
```
C:\MIPL\start_mipl_inspection.bat
```
This automatically boots both servers and opens your browser.

---

### Method 2: Manual Terminal Startup

Open **two separate terminals**:

#### Terminal 1 — AI Inference Engine (Port 8000)
```powershell
cd "c:\MIPL\AI_Badmal_backup (2)\AI_Badmal_backup\ai_server"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

#### Terminal 2 — Web Application Server (Port 8081)
```powershell
cd "c:\MIPL\AI_Badmal_backup (2)\AI_Badmal_backup\web_server"
python -m uvicorn main:app --host 127.0.0.1 --port 8081
```

---

## 🌐 URLs & Access
- **Web App / Dashboard**: [http://localhost:8081](http://localhost:8081)
- **AI Server Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Visual Model Test Sandbox**: Available directly on the **Surveillance Feed** page (`/admin/surveillance/`) via the **Upload & Test Model** button.

## 🔑 Default Login Credentials
| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@gmail.com` | `admin` |
| **Operator / User** | `user@gmail.com` | `user` |
| **Surveillance** | `s@gmail.com` | `s` |
