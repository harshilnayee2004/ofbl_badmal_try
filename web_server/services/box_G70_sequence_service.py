from models.box_model import Box
from sqlmodel import Session, select
from services.log_service import BoxLogService
from models.box_G70_inspection_model import BoxG70Inspection
from repositories.current_inspection_repositories import BoxInspectionRepository
from socket_controller.box_inspection_socket_controller import inspection_box_manager


class BoxG70SequenceService:

    @staticmethod
    async def process_result(db: Session,sequence_number: int, box_id: int, result: dict,box_log_service:BoxLogService):
        box_object = db.exec(
            select(Box).where(Box.id == box_id)
        ).first()

        if not box_object:
            return

        inspection = db.exec(
            select(BoxG70Inspection).where(
                BoxG70Inspection.id == box_object.box_g70_inspection_id
            )
        ).first()

        if not inspection:
            return

        match sequence_number:

            case 1:

                print(result)

                if result.get("BOX_NUMBER") is None:
                    await box_log_service.add_box_log(
                        description="Update Box Number Missing From The Top",
                        box_id=box_id
                    )
                else:
                    await box_log_service.add_box_log(
                        description=f"Update Box Number Is {result.get('BOX_NUMBER')}",
                        box_id=box_id
                    )

                if not all(
                        value is True
                        for key, value in result.items()
                        if key != "BOX_NUMBER"
                ):
                    inspection.stenciling = False
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Not Clear",
                        box_id=box_id
                    )
                else:
                    inspection.stenciling = True
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Clear",
                        box_id=box_id
                    )

                box_object.box_number = result.get("BOX_NUMBER")

                # ✅ Save first
                db.add(box_object)
                db.add(inspection)
                db.commit()
                db.refresh(box_object)
                db.refresh(inspection)

                # ✅ Send socket ONLY for sequence 1
                await inspection_box_manager.send_json({
                    "type": "box_update",
                    "object": {
                        "box_number": box_object.box_number,
                        "box_id": box_object.id,
                        "inspection_status": "Inspecting"
                    }
                })
                await inspection_box_manager.send_json({"type":"inspection_update","object":{"stenciling":inspection.stenciling,"paint":inspection.paint,"rusting":inspection.rusting,"explosive_sticker":inspection.explosive_sticker,"seals":inspection.seals}})


            case 2:

                print(result)

                if not all(
                        value is True
                        for key, value in result.items()
                ):
                    inspection.stenciling = False
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Not Clear",
                        box_id=box_id
                    )
                else:
                    if inspection.stenciling == True:
                        inspection.stenciling = True
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Clear",
                        box_id=box_id
                    )

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 3:

                print(result)
                # and result.get("IND.GOVT.EXPLOSIVE")
                if result.get("EXPLOSIVE_STICKER") and result.get("L1.2B"):
                    inspection.explosive_sticker = True
                    await box_log_service.add_box_log(
                        description="Update Explosive Sticker Is Proper",
                        box_id=box_id
                    )
                else:
                    inspection.explosive_sticker = False
                    await box_log_service.add_box_log(
                        description="Update Explosive Sticker Is Not Proper",
                        box_id=box_id
                    )

                if not all(
                        value is True
                        for key, value in result.items()
                        if key != "EXPLOSIVE_STICKER"
                            and key != "IND.GOVT.EXPLOSIVE"
                            and key != "L1.2B"
                ):

                    inspection.stenciling = False
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Not Clear",
                        box_id=box_id
                    )
                else:
                    if inspection.stenciling == True:
                        inspection.stenciling = True
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Clear",
                        box_id=box_id
                    )

                await inspection_box_manager.send_json({"type":"inspection_update","object":{"stenciling":inspection.stenciling,"paint":inspection.paint,"rusting":inspection.rusting,"explosive_sticker":inspection.explosive_sticker,"seals":inspection.seals}})
                

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 4:

                print(result)

                if not all(
                        value is True
                        for key, value in result.items()
                ):

                    inspection.stenciling = False
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Not Clear",
                        box_id=box_id
                    )
                else:
                    if inspection.stenciling == True:
                        inspection.stenciling = True
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Clear",
                        box_id=box_id
                    )

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 5:

                print(result)

                if result.get("SEAL") :
                    inspection.seals = True
                    await box_log_service.add_box_log(
                        description="Update Seals Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.seals = False
                    await box_log_service.add_box_log(
                        description="Update Seals Is Missing",
                        box_id=box_id
                    )

                if not all(
                        value is True
                        for key, value in result.items()
                        if key != "SEAL"
                ):

                    inspection.stenciling = False
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Not Clear",
                        box_id=box_id
                    )
                else:
                    if inspection.stenciling == True:
                        inspection.stenciling = True
                    await box_log_service.add_box_log(
                        description="Update Stenciling Is Clear",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type":"inspection_update","object":{"stenciling":inspection.stenciling,"paint":inspection.paint,"rusting":inspection.rusting,"explosive_sticker":inspection.explosive_sticker,"seals":inspection.seals}})
                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 6:

                print(result)

                if result.get("PACKING_SLIP") :
                    inspection.packing_slip = True
                    await box_log_service.add_box_log(
                        description="Update Packing Slip Is Proper",
                        box_id=box_id
                    )
                else:
                    inspection.packing_slip = False
                    await box_log_service.add_box_log(
                        description="Update Packing Slip Is Not Proper",
                        box_id=box_id
                    )


                if result.get("WOODEN_PALLET") :
                    inspection.top_wooden_pallet = True
                    await box_log_service.add_box_log(
                        description="Update Top Wooden Pallet Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.top_wooden_pallet = False
                    await box_log_service.add_box_log(
                        description="Update Top Wooden Pallet Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {"top_wooden_pallet": inspection.top_wooden_pallet,
                                                                    "packing_slip": inspection.packing_slip}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()
            case 7:

                print(result)

                if result.get("WHITE_FOAM_SHEET"):
                    inspection.foam = True
                    await box_log_service.add_box_log(
                        description="Update Foam Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.foam = False
                    await box_log_service.add_box_log(
                        description="Update Foam Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "foam": inspection.foam}})


                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()
            case 8:

                print(result)

                if result.get("BOTTOM_WOODEN_PALATE"):
                    inspection.bottom_wooden_pallet = True
                    await box_log_service.add_box_log(
                        description="Update Bottom Wooden Pallet Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.bottom_wooden_pallet = False
                    await box_log_service.add_box_log(
                        description="Update Bottom Wooden Pallet Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "bottom_wooden_pallet": inspection.bottom_wooden_pallet}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()
            case 9:

                print(result)

                if result.get("BOTTOM_WOODEN_GRID"):
                    inspection.bottom_wooden_grid = True
                    await box_log_service.add_box_log(
                        description="Update Bottom Wooden Grid Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.bottom_wooden_grid = False
                    await box_log_service.add_box_log(
                        description="Update Bottom Wooden Grid Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "bottom_wooden_grid": inspection.bottom_wooden_grid}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()
            case 10:

                print(result)

                if result.get("CONTAINER_COUNT_50"):
                    inspection.container_count_50 = True
                    await box_log_service.add_box_log(
                        description="Update Container Count Is 50",
                        box_id=box_id
                    )
                else:
                    inspection.container_count_50 = False
                    await box_log_service.add_box_log(
                        description="Update Container Count Is Not 50",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "container_count_50": inspection.container_count_50}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()
