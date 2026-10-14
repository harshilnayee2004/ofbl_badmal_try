from repositories.current_inspection_repositories import BoxInspectionRepository
class PhysicalButtonService:
    def box_button_pressed(self):
        current_inspection_status = BoxInspectionRepository.inspection_command
        
        if current_inspection_status == "Continue":
            BoxInspectionRepository.inspection_command = "Paused"
            return "Paused"
        elif current_inspection_status == "Paused":
            BoxInspectionRepository.inspection_command = "Continue"
            return "Continue"
        elif current_inspection_status == "Stopped":
            BoxInspectionRepository.inspection_command = "Continue"
            return "Continue"

    def fuze_button_pressed(self):
        pass