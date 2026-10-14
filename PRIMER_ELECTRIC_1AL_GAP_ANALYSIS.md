# Primer Electric 1A/L - System Requirements & Gap Analysis Documentation

**Target Product:** Primer Electric 1A/L Inspection System  
**Inspection Hierarchy:** Carrier 6A/L (Outer Packaging) $\rightarrow$ H2A Box (Inner Packaging) $\rightarrow$ Primer Electric 1A/L (Unit Level)  
**Workspace Path:** `c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/`

---

## 1. Master Testing Parameter Mapping (1 to 19)

| S.No | Testing Parameter | Inspection Level | Definition & Criteria | Dataset Status | Architectural Action | Impacted Files |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Sealed Box** | Acceptance for Carrier 6A/L | Check sealing integrity & presence | Proper | **Re-define / Create Workflow** | [box_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/box_service.py), [inference_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/inference_service.py) |
| **2** | **Damage Box** | Acceptance for Carrier 6A/L | Detect dents, cracks, or surface damage | *Not Proper (Needs Rusting & Painting Dataset)* | **Re-define / Create Model + Prompt** | `ai_server/prompts/carrier_6a_prompts/`, [rfdetr_processor.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/processors/rfdetr_processor.py) |
| **3** | **Rusty Box** | Acceptance for Carrier 6A/L | Check rust / surface corrosion on outer box | *Not Proper (Needs Rusting & Painting Dataset)* | **Re-define / Create Model + Prompt** | `ai_server/prompts/carrier_6a_prompts/`, `ai_server/ai_models/` |
| **4** | **Incorrect Stenciling on Box** | Acceptance for Carrier 6A/L | OCR stenciling accuracy and format match | Proper | **Re-define / Create Prompt Sequence** | `ai_server/prompts/carrier_6a_prompts/sequence_ocr.txt`, [inspect_box_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/inspect_box_service.py) |
| **5** | **Explosive Label Missing** | Acceptance for Carrier 6A/L | Verify presence and alignment of hazard sticker | Proper | **Re-define / Create Detection Logic** | `ai_server/prompts/carrier_6a_prompts/`, [inspect_box_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/inspect_box_service.py) |
| **6** | **Incorrect Stenciling on Box** | Acceptance for H2A Box | OCR verification across 5 sides of the box | Proper | **Re-define / Create 5-Side Sequence** | `ai_server/prompts/h2a_box_prompts/`, `web_server/services/box_H2A_sequence_service.py` |
| **7** | **Explosive Label Missing** | Acceptance for H2A Box | Explosive label is missing or not on H2A box | Proper | **Re-define / Create Prompt Sequence** | `ai_server/prompts/h2a_box_prompts/`, `web_server/services/box_H2A_sequence_service.py` |
| **8** | **Wooden Sheet** | Acceptance for H2A Box | Check presence of top/outer protective wooden sheet | Proper | **Re-define / Create Prompt Sequence** | `ai_server/prompts/h2a_box_prompts/sequence_wooden_sheet.txt` |
| **9** | **Packing Slip** | Acceptance for H2A Box | Check packing slip (white/brown color) is present | Proper | **Re-define / Create Prompt Sequence** | `ai_server/prompts/h2a_box_prompts/sequence_packing_slip.txt` |
| **10** | **Cotton Sheet** | Acceptance for H2A Box | Check cotton cushioning sheet is present | Proper | **Re-define / Create Prompt Sequence** | `ai_server/prompts/h2a_box_prompts/sequence_cotton_sheet.txt` |
| **11** | **More / Less Quantity in Box** | Acceptance for H2A Box | Count total number of primers in the box grid | Proper | **Re-define / Create Counting Model** | `ai_server/ai_models/primer_count.pth`, [counting_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/counting_service.py) |
| **12** | **Wooden Sheet (18 Holes)** | Acceptance for H2A Box | Check 2 wooden sheets with 18 holes are present | Proper | **Re-define / Create Prompt / Detector** | `ai_server/prompts/h2a_box_prompts/sequence_18_holes.txt` |
| **13** | **Rust & Peeling Paint Inside** | Acceptance for H2A Box | Check internal box walls for rust and paint peeling | *Not Proper (Needs Interior Rust/Paint Dataset)* | **Re-define / Create Model + Prompt** | `ai_server/prompts/h2a_box_prompts/sequence_interior.txt` |
| **14** | **Improper Cleanliness Appearance** | Primer Electric 1A/L | Check primer cleanliness & foreign contaminants | *Improper Primer Not Given (Dataset Gap)* | **Re-define / Create Prompt + Dataset** | `ai_server/prompts/primer_1al_prompts/sequence_cleanliness.txt` |
| **15** | **Incorrect LOT NUMBER** | Primer Electric 1A/L | Verify lot number presence and format on primer body | Proper | **Re-define / Create OCR Prompt** | `ai_server/prompts/primer_1al_prompts/sequence_lot_ocr.txt` |
| **16** | **Crack/Damage on Magazine** | Primer Electric 1A/L | Check for cracks/damage on primer magazine head | *Damaged Primer Not Given (Dataset Gap)* | **Re-define / Create Prompt + Dataset** | `ai_server/prompts/primer_1al_prompts/sequence_damage.txt` |
| **17** | **Paper Liner Damage** | Primer Electric 1A/L | Check paper liner intactness & gunpowder spillage | Proper | **Re-define / Create Detection Logic** | `ai_server/prompts/primer_1al_prompts/sequence_paper_liner.txt` |
| **18** | **Absence/Damage of Rubber Ring** | Primer Electric 1A/L | Check rubber ring presence, damage, or seating error | Proper | **Re-define / Create Detection / Prompt** | `ai_server/prompts/primer_1al_prompts/sequence_rubber_ring.txt` |
| **19** | **Improper Assembly of Magazine** | Primer Electric 1A/L | Check improper assembly of magazine to primer body | *Doubt / Clarification Required* | **Re-define / Create Sequence Logic** | `ai_server/prompts/primer_1al_prompts/sequence_assembly.txt` |

---

## 2. Category 1: Feature Exists & No Need to Touch It (Keep As-Is)

The following modules represent foundational infrastructure, camera video streams, device control, authentication, database connections, and AI inference engines that are completely reusable across any ordnance or primer inspection.

### 2.1. Authentication, Security & User Management
* **Description:** User login, session management, password hashing, and role-based access control (Admin / Inspector / Surveillance).
* **Associated Files:**
  * [web_server/core/security.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/core/security.py)
  * [web_server/core/deps.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/core/deps.py)
  * [web_server/core/database.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/core/database.py)
  * [web_server/core/config.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/core/config.py)
  * [web_server/models/user_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/user_model.py)
  * [web_server/controllers/auth_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/auth_controller.py)
  * [web_server/controllers/manage_user_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/manage_user_controller.py)
  * [web_server/services/user_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/user_service.py)
  * [web_server/templates/login.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/login.html)
  * [web_server/templates/admin/users.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/admin/users.html)

### 2.2. Camera Streaming, PTZ, Video Recording & Hardware Controls
* **Description:** RTSP multi-camera feed ingestion, live OpenCV capture, video recording with FFmpeg overlays, PTZ controls, physical hardware button listeners, and motor rotation triggers.
* **Associated Files:**
  * [web_server/models/camera_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/camera_model.py)
  * [web_server/controllers/camera_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/camera_controller.py)
  * [web_server/controllers/motor_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/motor_controller.py)
  * [web_server/controllers/ptz_control_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/ptz_control_controller.py)
  * [web_server/controllers/physical_button_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/physical_button_controller.py)
  * [web_server/controllers/surveillance_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/surveillance_controller.py)
  * [web_server/services/camera_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/camera_service.py)
  * [web_server/services/stream_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/stream_service.py)
  * [web_server/services/stream_manager.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/stream_manager.py)
  * [web_server/services/video_recording_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/video_recording_service.py)
  * [web_server/services/ptz_control_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/ptz_control_service.py)
  * [web_server/services/physical_button_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/physical_button_service.py)
  * [web_server/services/background_services.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/background_services.py)
  * [web_server/templates/admin/cameras.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/admin/cameras.html)
  * [web_server/templates/admin/surveillance.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/admin/surveillance.html)

### 2.3. AI Engine Core (VLM & RF-DETR Execution Engine)
* **Description:** Base wrappers for Qwen2.5-VL / QwenVLM inference and RF-DETR object detector execution.
* **Associated Files:**
  * [ai_server/processors/qwenVLM8b_L4_vllm_processor.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/processors/qwenVLM8b_L4_vllm_processor.py)
  * [ai_server/processors/qwenVLM8b_processor.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/processors/qwenVLM8b_processor.py)
  * [ai_server/processors/rfdetr_processor.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/processors/rfdetr_processor.py)
  * [ai_server/controllers/inference_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/controllers/inference_controller.py)
  * [ai_server/repositories/processors_repository.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/repositories/processors_repository.py)

---

## 3. Category 2: Features That Need Little Tweaks (Minor Modifications)

These modules are structurally in place but need schema adaptations, dropdown updates, label changes, and new inspection status bindings for Primer Electric 1A/L.

### 3.1. Lot Creation, Quantities & Sampling Logic
* **Modifications Needed:**
  * Update `fuze_type` / `item_type` selection dropdown to include `"Primer Electric 1A/L"`.
  * Set default lot size counts (Total Primers in Lot, Carrier 6A/L Count, H2A Box Count, Sampling Size for Carrier, H2A, and Primer unit inspection).
  * Associate the Carrier 6A/L and H2A Box types.
* **Associated Files:**
  * [web_server/models/lot_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/lot_model.py)
  * [web_server/schemas/lot_dto.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/schemas/lot_dto.py)
  * [web_server/services/lot_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/lot_service.py)
  * [web_server/controllers/lot_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/lot_controller.py)
  * [web_server/templates/user/manage_lots.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/user/manage_lots.html)
  * [web_server/static/js/user/lot_management.js](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/static/js/user/lot_management.js)

### 3.2. Real-Time WebSockets & Inspection State Repositories
* **Modifications Needed:**
  * Adjust repository state holding variables (`current_wait_time`, `current_instruction`, `inspection_command`) to support the 3-level hierarchy (Carrier $\rightarrow$ H2A Box $\rightarrow$ Primer Unit).
* **Associated Files:**
  * [web_server/repositories/current_inspection_repositories.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/repositories/current_inspection_repositories.py)
  * [web_server/socket_controller/box_inspection_socket_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/socket_controller/box_inspection_socket_controller.py)
  * [web_server/socket_controller/fuze_inspection_socket_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/socket_controller/fuze_inspection_socket_controller.py)
  * [web_server/socket_controller/lot_inspection_socket_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/socket_controller/lot_inspection_socket_controller.py)

### 3.3. Report Generation (Excel & PDF)
* **Modifications Needed:**
  * Add Excel sheets and PDF inspection checklist templates rendering the 5 parameters of Carrier 6A/L, 8 parameters of H2A Box, and 6 parameters of Primer Electric 1A/L.
* **Associated Files:**
  * [web_server/services/report_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/report_service.py)
  * [web_server/controllers/report_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/report_controller.py)

### 3.4. User Dashboard & Summary Counters
* **Modifications Needed:**
  * Update dashboard cards and table headers from "Fuze" to "Primer Electric 1A/L" or generic "Ordnance / Primer Inspection".
* **Associated Files:**
  * [web_server/templates/user/dashboard.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/user/dashboard.html)
  * [web_server/templates/admin/dashboard.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/admin/dashboard.html)
  * [web_server/controllers/user_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/user_controller.py)

---

## 4. Category 3: Features That Must Be Re-Defined / Newly Created

These are the primary new modules required to satisfy the 19 inspection parameters from the requirement sheet.

### 4.1. Database Models (SQLModel)
* **New / Redefined Models to Implement:**
  1. `Carrier6ALInspection`: Table storing results for Carrier 6A/L:
     * `sealed_box: Optional[bool]` (Param 1)
     * `damage_box: Optional[bool]` (Param 2)
     * `rusty_box: Optional[bool]` (Param 3)
     * `stenciling: Optional[bool]` (Param 4)
     * `explosive_label: Optional[bool]` (Param 5)
  2. `BoxH2AInspection`: Table storing results for H2A Box:
     * `stenciling_5_sides: Optional[bool]` (Param 6)
     * `explosive_label: Optional[bool]` (Param 7)
     * `wooden_sheet: Optional[bool]` (Param 8)
     * `packing_slip: Optional[bool]` (Param 9)
     * `cotton_sheet: Optional[bool]` (Param 10)
     * `primer_quantity_count: Optional[bool]` (Param 11)
     * `wooden_sheet_18_holes: Optional[bool]` (Param 12)
     * `interior_rust_peeling_paint: Optional[bool]` (Param 13)
  3. `PrimerElectric1ALInspection`: Table storing unit-level inspection:
     * `cleanliness_appearance: Optional[bool]` (Param 14)
     * `lot_number_match: Optional[bool]` (Param 15)
     * `magazine_crack_damage: Optional[bool]` (Param 16)
     * `paper_liner_damage_spillage: Optional[bool]` (Param 17)
     * `rubber_ring_assembly: Optional[bool]` (Param 18)
     * `magazine_assembly: Optional[bool]` (Param 19)
* **Target Files to Create/Update:**
  * `web_server/models/carrier_6al_inspection_model.py` **[NEW]**
  * `web_server/models/box_h2a_inspection_model.py` **[NEW]**
  * `web_server/models/primer_1al_inspection_model.py` **[NEW]**
  * Update foreign keys in [web_server/models/box_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/box_model.py) and [web_server/models/fuze_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/fuze_model.py) (or `primer_model.py`).

### 4.2. Business Logic Sequence Services
* **New Sequence Orchestration Services:**
  1. `Carrier6ALSequenceService` & `Carrier6ALInspectionService`:
     * Stepper loop controlling camera, turntable rotation, capturing images for sealing, damage/rust analysis, OCR text extraction, and label detection.
  2. `BoxH2ASequenceService` & `BoxH2AInspectionService`:
     * Handles 5-side OCR capture sequence, packing slip color verification (white/brown), presence of wooden sheets, 18-hole sheet presence, cotton sheet presence, count verification, and internal box wall rust/paint inspection.
  3. `Primer1ALSequenceService` & `Primer1ALInspectionService`:
     * Handles 360° rotational imaging of the primer unit: cleanliness check, LOT engraving check, magazine surface cracks, paper liner intactness + powder spillage detection, rubber ring seating, and magazine-to-body alignment check.
* **Target Files to Create:**
  * `web_server/services/carrier_6al_sequence_service.py` **[NEW]**
  * `web_server/services/carrier_6al_inspection_service.py` **[NEW]**
  * `web_server/services/box_h2a_sequence_service.py` **[NEW]**
  * `web_server/services/box_h2a_inspection_service.py` **[NEW]**
  * `web_server/services/primer_1al_sequence_service.py` **[NEW]**
  * `web_server/services/primer_1al_inspection_service.py` **[NEW]**

### 4.3. AI Server Prompts & Inference Handlers
* **Prompt Sets to Create:**
  * `ai_server/prompts/carrier_6a_prompts/`:
    * `sequence_1_sealing.txt`
    * `sequence_2_damage.txt`
    * `sequence_3_rust.txt`
    * `sequence_4_ocr_stenciling.txt`
    * `sequence_5_explosive_label.txt`
  * `ai_server/prompts/h2a_box_prompts/`:
    * `sequence_1_to_5_ocr_5_sides.txt`
    * `sequence_6_explosive_label.txt`
    * `sequence_7_wooden_sheet.txt`
    * `sequence_8_packing_slip.txt`
    * `sequence_9_cotton_sheet.txt`
    * `sequence_10_quantity_count.txt`
    * `sequence_11_wooden_sheet_18_holes.txt`
    * `sequence_12_interior_rust_peeling_paint.txt`
  * `ai_server/prompts/primer_1al_prompts/`:
    * `sequence_1_cleanliness.txt`
    * `sequence_2_lot_number_ocr.txt`
    * `sequence_3_magazine_crack_damage.txt`
    * `sequence_4_paper_liner_spillage.txt`
    * `sequence_5_rubber_ring_assembly.txt`
    * `sequence_6_magazine_assembly.txt`
* **Target Files to Update in AI Server:**
  * [ai_server/services/inspect_box_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/inspect_box_service.py) (Add `inspect_carrier_6a` and `inspect_box_h2a`)
  * [ai_server/services/inspect_fuze_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/inspect_fuze_service.py) (Add `inspect_primer_1al`)
  * [ai_server/controllers/inspect_box_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/controllers/inspect_box_controller.py)
  * [ai_server/controllers/inspect_fuze_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/controllers/inspect_fuze_controller.py)

### 4.4. Frontend Inspection Views & Client-Side JS
* **Modifications & New Handlers:**
  * Render checklist tiles and manual checkbox overrides dynamically for all 19 parameters.
  * Multi-view stenciling feedback for the 5 sides of Box H2A.
* **Target Files to Update / Create:**
  * [web_server/templates/user/inspect_box/inspection.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/user/inspect_box/inspection.html)
  * [web_server/static/js/user/inspect_box/box_inspection_main.js](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/static/js/user/inspect_box/box_inspection_main.js)
  * [web_server/templates/user/inspect_fuze/inspection.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/user/inspect_fuze/inspection.html)
  * [web_server/static/js/user/inspect_fuze/fuze_inspection_main.js](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/static/js/user/inspect_fuze/fuze_inspection_main.js)

---

## 5. Category 4: Features That Must Be Removed / Deprecated

If this deployment is transitioning strictly to **Primer Electric 1A/L**, the following legacy models, controllers, and services are irrelevant to the current requirements and should be removed or deprecated:

### 5.1. Water Immersion Test Subsystem (Not required for Primer Electric 1A/L)
* **Reason for Removal:** The requirement sheet for Primer Electric 1A/L does not include a water immersion / air bubble leak test (which was specific to Fuze 4A ND).
* **Associated Files to Remove / Disable:**
  * [web_server/services/water_immersion_test_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/water_immersion_test_service.py)
  * [web_server/controllers/water_immersion_test_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/controllers/water_immersion_test_controller.py)
  * [web_server/templates/user/water_immersion_test.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/user/water_immersion_test.html)
  * [web_server/templates/user/water_immersion_selection.html](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/templates/user/water_immersion_selection.html)
  * [web_server/static/js/user/water_immersion_test.js](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/static/js/user/water_immersion_test.js)
  * [web_server/socket_controller/water_immersion_test_socket_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/socket_controller/water_immersion_test_socket_controller.py)
  * [ai_server/services/bubble_predection_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/bubble_predection_service.py)
  * [ai_server/services/water_immersion_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/services/water_immersion_service.py)
  * [ai_server/controllers/bubble_prediction_controller.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/controllers/bubble_prediction_controller.py)
  * [ai_server/controllers/water_immersion_test.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/ai_server/controllers/water_immersion_test.py)
  * `ai_server/ai_models/bubble_prediction.pth`

### 5.2. Legacy Fuze & Box Implementations (Can be cleaned up if not multi-product)
* **Associated Files:**
  * **Legacy Fuzes (117MK, 2BND, 4AND):**
    * [web_server/models/fuze_117MK_inspection_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/fuze_117MK_inspection_model.py), [fuze_2BND_inspection_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/fuze_2BND_inspection_model.py), [fuze_4AND_inspection_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/fuze_4AND_inspection_model.py)
    * [web_server/services/fuze_117MK_inspection_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/fuze_117MK_inspection_service.py), `fuze_117MK_sequence_service.py`
    * [web_server/services/fuze_2BND_inspection_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/fuze_2BND_inspection_service.py), `fuze_2BND_sequence_service.py`
    * [web_server/services/fuze_4AND_inspection_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/fuze_4AND_inspection_service.py), `fuze_4AND_sequence_service.py`
    * `ai_server/prompts/fuze_117mk_prompts/`, `fuze_2bnd_prompts/`, `fuze_4and_prompts/`
    * `ai_server/ai_models/safety_pin_model.pth`
  * **Legacy Boxes (G70, M104):**
    * [web_server/models/box_G70_inspection_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/box_G70_inspection_model.py), [box_M104_inspection_model.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/models/box_M104_inspection_model.py)
    * [web_server/services/box_G70_inspection_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/box_G70_inspection_service.py), `box_G70_sequence_service.py`
    * [web_server/services/box_M104_inspection_service.py](file:///c:/Users/admin/Desktop/Dhvanit/AI_Budmal/CURRENT_VERSION/web_server/services/box_M104_inspection_service.py), `box_M104_sequence_service.py`, `box_M104_counting_service.py`
    * `ai_server/prompts/g70_box_prompts/`, `m104_box_prompts/`
    * `ai_server/ai_models/M104_box_counting.pth`, `M104_seal.pth`, `C07_container_counting.pth`

---

## 6. Dataset & AI Model Training Action Items (From Requirements Sheet)

The requirement table explicitly notes dataset generation prerequisites for specific parameters:

1. **Parameters 2 & 3 (Carrier 6A/L - Damage Box & Rusty Box):**
   * *Status:* Dataset Not Proper.
   * *Action:* Collect/augment imagery for box dents, surface scratches, corrosion/rust on Carrier 6A/L exterior metal surfaces.
2. **Parameter 13 (H2A Box - Rust & Peeling Paint Inside):**
   * *Status:* Dataset Not Proper.
   * *Action:* Collect/generate dataset of internal surface defects, flaking/peeling paint, and internal rusting inside Box H2A.
3. **Parameter 14 (Primer Electric 1A/L - Improper Cleanliness Appearance):**
   * *Status:* Improper Primer Not Given.
   * *Action:* Collect samples of dirty/oil-stained/foreign-particle contaminated primer bodies.
4. **Parameter 16 (Primer Electric 1A/L - Crack/Damage on Magazine):**
   * *Status:* Damaged Primer Not Given.
   * *Action:* Collect/generate cracked/deformed magazine heads.
5. **Parameter 19 (Primer Electric 1A/L - Improper Assembly of Magazine to Primer Body):**
   * *Status:* Marked as "doubt".
   * *Action:* Clarify mechanical inspection tolerances (thread gap, misalignment angle, or tilt) to define the AI acceptance criteria.
