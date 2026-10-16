========================================================================
   MIPL Ordnance Quality Assurance & AI Video Inspection System
========================================================================

QUICK START GUIDE FOR NEW PC:
------------------------------------------------------------------------

PREREQUISITE:
- Python 3.10, 3.11, or 3.12 installed (Make sure "Add Python to PATH" was checked during install).

STEP 1: INSTALL DEPENDENCIES (One-Time Setup)
- Double-click: "1_install_dependencies.bat"
  (This automatically installs PyTorch, RF-DETR, FastAPI, and all required packages).

STEP 2: RUN THE SYSTEM
- Double-click: "START_SYSTEM.bat"
  (This launches both the AI Server on Port 8000 and the Web Server on Port 8081,
   and automatically opens your browser to http://localhost:8081).

  OR start them individually:
  - Double-click "2_start_ai_server.bat"
  - Double-click "3_start_web_server.bat"

STEP 3: LOGIN CREDENTIALS
- Admin Login:
  Email:    admin@gmail.com
  Password: admin

- Inspector/User Login:
  Email:    user@gmail.com
  Password: user

------------------------------------------------------------------------
WHAT IS INCLUDED IN THIS PACKAGE:
------------------------------------------------------------------------
- ai_server/
  └── ai_models/ (All 8 trained RF-DETR .pth model weights are included!)
      1. Carrier6AL_Explosive_Seal.pth
      2. carrier_rust_checkpoint_best_total.pth
      3. H2A_Explosive_Seal.pth
      4. h2a_rust_checkpoint_best_total.pth
      5. Inner_H2A_Box.pth
      6. Primer.pth
      7. Primer_Count.pth
      8. Primer_Paint_checkpoint_best_total.pth

- web_server/
  ├── .env          (Pre-configured with SQLite and AI Server URL)
  └── badmal_dev.db (Pre-seeded database with users and tables ready)

========================================================================
