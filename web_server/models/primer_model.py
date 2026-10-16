import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Primer(SQLModel, table=True):
    __tablename__ = "fuzes"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    lot_id: Optional[int] = Field(default=None, foreign_key="lots.id")
    box_id: Optional[int] = Field(default=None, foreign_key="boxes.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    primer_type: Optional[str] = Field(default="Primer Electric 1A/L", alias="fuze_type")
    sequence_number: Optional[int] = Field(default=None)
    files_path: Optional[str] = Field(default=None)
    primer_number: Optional[int] = Field(default=None, alias="fuze_number")
    acceptance_status: Optional[bool] = Field(default=None)
    primer_inspection_status: str = Field(default="Pending", alias="fuze_inspection_status")
    primer_1al_inspection_id: Optional[int] = Field(default=None, foreign_key="primer_1al_inspections.id")
    start_time: Optional[datetime.datetime] = Field(default=None)
    end_time: Optional[datetime.datetime] = Field(default=None)

    @property
    def fuze_type(self) -> Optional[str]:
        return self.primer_type

    @fuze_type.setter
    def fuze_type(self, val: Optional[str]):
        self.primer_type = val

    @property
    def fuze_number(self) -> Optional[int]:
        return self.primer_number

    @fuze_number.setter
    def fuze_number(self, val: Optional[int]):
        self.primer_number = val

    @property
    def fuze_inspection_status(self) -> str:
        return self.primer_inspection_status

    @fuze_inspection_status.setter
    def fuze_inspection_status(self, val: str):
        self.primer_inspection_status = val

# Backward compatibility alias
Fuze = Primer
