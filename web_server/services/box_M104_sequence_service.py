from models.box_model import Box
from sqlmodel import Session, select
from services.log_service import BoxLogService
from models.box_M104_inspection_model import BoxM104Inspection
from socket_controller.box_inspection_socket_controller import inspection_box_manager


class BoxM104SequenceService:

    @staticmethod
    async def process_result(db: Session,sequence_number: int, box_id: int, result: dict,box_log_service:BoxLogService):
        box_object = db.exec(
            select(Box).where(Box.id == box_id)
        ).first()

        if not box_object:
            return

        inspection = db.exec(
            select(BoxM104Inspection).where(
                BoxM104Inspection.id == box_object.box_m104_inspection_id
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
                
                    #             {
                    # "UNIV": true,
                    # "BOX_NO_VALID": true,
                    # "FUZE 117": true,
                    # "AV_MASS_KG_18_70": true,
                    # "BOX_NUMBER": 1,
                    # "TO": true,
                    # "CONNANDANT": true,
                    # "CADPULOAON": true,
                    # "FROM": true,
                    # "CCN": true,
                    # "OFBL": true,
                    # "SEAL": false
                    # }

                if not result.get("UNIV"):
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

                if result.get("SEALS"):
                    inspection.seals = True
                    await box_log_service.add_box_log(
                        description="Update Seals Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.seals = False
                    await box_log_service.add_box_log(
                        description="Update Seals    Is Missing",
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
                if inspection.stenciling:
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
                await inspection_box_manager.send_json({"type":"inspection_update","object":{"stenciling":inspection.stenciling,"paint":inspection.paint,"rusting":inspection.rusting,"explosive_sticker":inspection.explosive_sticker,"seals":inspection.seals}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 3:

                print(result)

                if result.get("Orange_Sticker"):
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
                if inspection.stenciling:
                    if result.get("FUZE 117"):
                        inspection.stenciling = True
                        await box_log_service.add_box_log(
                            description="Update Stenciling Is Clear",
                            box_id=box_id
                        )
                    else:
                        inspection.stenciling = False
                        await box_log_service.add_box_log(
                            description="Update Stenciling Is Not Clear",
                            box_id=box_id
                        )

                await inspection_box_manager.send_json({"type":"inspection_update","object":{"stenciling":inspection.stenciling,"paint":inspection.paint,"rusting":inspection.rusting,"explosive_sticker":inspection.explosive_sticker,"seals":inspection.seals}})
                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

               

            case 4:

                print(result)
                if inspection.stenciling:
                    if result.get("UNIV"):
                        inspection.stenciling = True
                        await box_log_service.add_box_log(
                            description="Update Stenciling Is Clear",
                            box_id=box_id
                        )
                    else:
                        inspection.stenciling = False
                        await box_log_service.add_box_log(
                            description="Update Stenciling Is Not Clear",
                            box_id=box_id
                        )

                    if result.get("BOX_NUMBER") == box_object.box_number:
                        inspection.stenciling = True
                        await box_log_service.add_box_log(
                            description="Update Stenciling Is Clear",
                            box_id=box_id
                        )
                    else:
                        inspection.stenciling = False
                        await box_log_service.add_box_log(
                            description="Update Stenciling Is Not Clear",
                            box_id=box_id
                        )

                    

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 5:

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


                if result.get("WHITE_FOAM") :
                    inspection.top_foam = True
                    await box_log_service.add_box_log(
                        description="Update Top Foam Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.top_foam = False
                    await box_log_service.add_box_log(
                        description="Update Top Foam Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {"top_foam": inspection.top_foam,
                                                                    "packing_slip": inspection.packing_slip}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()
            case 7:

                print(result)

                if result.get("Container_count") == 10:
                    inspection.container_count_10 = True
                    await box_log_service.add_box_log(
                        description="Update Container Count Is 10",
                        box_id=box_id
                    )
                else:
                    inspection.container_count_10 = False
                    await box_log_service.add_box_log(
                        description="Update Container Count Is Not 10",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "container_count_10": inspection.container_count_10}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 8:

                print(result)

                if result.get("PARTITION"):
                    inspection.wooden_grid = True
                    await box_log_service.add_box_log(
                        description="Update Wooden Grid Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.wooden_grid = False
                    await box_log_service.add_box_log(
                        description="Update Wooden Grid Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "wooden_grid": inspection.wooden_grid}})


                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()

            case 9:

                print(result)

                if result.get("WHITE_FOAM"):
                    inspection.bottom_foam = True
                    await box_log_service.add_box_log(
                        description="Update Bottom Foam Is Present",
                        box_id=box_id
                    )
                else:
                    inspection.bottom_foam = False
                    await box_log_service.add_box_log(
                        description="Update Bottom Wooden Pallet Is Missing",
                        box_id=box_id
                    )
                await inspection_box_manager.send_json({"type": "inspection_update",
                                                        "object": {
                                                            "bottom_foam": inspection.bottom_foam}})

                # Save only (no socket)
                db.add(box_object)
                db.add(inspection)
                db.commit()