# Legacy wrapper for primer_controller
from controllers.primer_controller import router, legacy_fuze_router
# Export legacy_fuze_router as router so main.py continues working seamlessly
router = legacy_fuze_router
