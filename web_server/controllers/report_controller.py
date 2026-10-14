from sqlmodel import Session
from core.database import get_db
from fastapi.responses import StreamingResponse
from services.report_service import ReportService
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

# -------------------------------------------------------------
# 1. CARRIER 6A/L (LEVEL 1) REPORT ENDPOINTS
# -------------------------------------------------------------

@router.get("/carrier/{carrier_id}/excel")
async def download_carrier_report(
    carrier_id: int,
    db: Session = Depends(get_db)
):
    try:
        excel_file = await ReportService.generate_carrier_excel_report(db, carrier_id)
        headers = {
            'Content-Disposition': f'attachment; filename="carrier_report_{carrier_id}.xlsx"'
        }
        return StreamingResponse(
            iter([excel_file.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/carrier/{carrier_id}/pdf")
async def download_carrier_pdf_report(
    carrier_id: int,
    db: Session = Depends(get_db)
):
    try:
        pdf_file = await ReportService.generate_carrier_pdf_report(db, carrier_id)
        headers = {
            'Content-Disposition': f'attachment; filename="carrier_report_{carrier_id}.pdf"'
        }
        return StreamingResponse(
            iter([pdf_file.getvalue()]),
            media_type="application/pdf",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# 2. BOX H2A & LEGACY BOX (LEVEL 2) REPORT ENDPOINTS
# -------------------------------------------------------------

@router.get("/box/{box_id}/excel")
async def download_box_report(
    box_id: int,
    db: Session = Depends(get_db)
):
    try:
        excel_file = await ReportService.generate_box_excel_report(db, box_id)
        headers = {
            'Content-Disposition': f'attachment; filename="box_report_{box_id}.xlsx"'
        }
        return StreamingResponse(
            iter([excel_file.getvalue()]), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/box/{box_id}/pdf")
async def download_box_pdf_report(
    box_id: int,
    db: Session = Depends(get_db)
):
    try:
        pdf_file = await ReportService.generate_box_pdf_report(db, box_id)
        headers = {
            'Content-Disposition': f'attachment; filename="box_report_{box_id}.pdf"'
        }
        return StreamingResponse(
            iter([pdf_file.getvalue()]), 
            media_type="application/pdf",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# 3. PRIMER ELECTRIC 1A/L & FUZE (LEVEL 3) REPORT ENDPOINTS
# -------------------------------------------------------------

@router.get("/fuze/{fuze_id}/excel")
@router.get("/primer/{fuze_id}/excel")
async def download_fuze_report(
    fuze_id: int,
    db: Session = Depends(get_db)
):
    try:
        excel_file = await ReportService.generate_fuze_excel_report(db, fuze_id)
        headers = {
            'Content-Disposition': f'attachment; filename="primer_unit_report_{fuze_id}.xlsx"'
        }
        return StreamingResponse(
            iter([excel_file.getvalue()]), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fuze/{fuze_id}/pdf")
@router.get("/primer/{fuze_id}/pdf")
async def download_fuze_pdf_report(
    fuze_id: int,
    db: Session = Depends(get_db)
):
    try:
        pdf_file = await ReportService.generate_fuze_pdf_report(db, fuze_id)
        headers = {
            'Content-Disposition': f'attachment; filename="primer_unit_report_{fuze_id}.pdf"'
        }
        return StreamingResponse(
            iter([pdf_file.getvalue()]), 
            media_type="application/pdf",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# 4. COMPREHENSIVE LOT EXPORT ZIP (3 TIERS)
# -------------------------------------------------------------

@router.get("/lot/{lot_id}/export-zip")
async def download_lot_zip_report(
    lot_id: int,
    db: Session = Depends(get_db)
):
    try:
        zip_file = await ReportService.generate_lot_export_zip(db, lot_id)
        headers = {
            'Content-Disposition': f'attachment; filename="lot_report_{lot_id}.zip"'
        }
        return StreamingResponse(
            iter([zip_file.getvalue()]), 
            media_type="application/zip",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

