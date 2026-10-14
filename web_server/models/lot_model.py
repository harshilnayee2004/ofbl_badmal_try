import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class Lot(SQLModel, table=True):
    __tablename__ = "lots"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    lot_number: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    inspection_status: str = Field(default="Pending")
    box_inspection_status: str = Field(default="Pending")
    primer_inspection_status: str = Field(default="Pending")
    files_path: str=Field(default=None)

    number_of_carrier: Optional[int] = Field(default=None)
    number_of_carrier_to_inspect: Optional[int] = Field(default=None)
    carrier_type: Optional[str] = Field(default=None)
    carrier_current_sequence: Optional[int] = Field(default=1)
    carrier_count_confirmation: Optional[int] = Field(default=0)
    carrier_inspection_status: str = Field(default="Pending")
    carrier_acceptance_status: str = Field(default="Pending")

    number_of_box: Optional[int] = Field(default=None)
    number_of_primer: Optional[int] = Field(default=None)
    number_of_box_to_inspect: Optional[int] = Field(default=None)
    number_of_primer_to_inspect: Optional[int] = Field(default=None)
    box_type: Optional[str] = Field(default=None)
    # container_type: Optional[str] = Field(default=None) // are anything thhere called containers? cuz I am seeing carriers and containers both in this file
    primer_type: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    total_quantity: Optional[int] = Field(default=None)
    sampling_plan: Optional[str] = Field(default=None)

    box_current_sequence: Optional[int] = Field(default=None)
    primer_current_sequence: Optional[int] = Field(default=None)

    box_count_confirmation: Optional[int] = Field(default=0)
    primer_count_confirmation: Optional[int] = Field(default=0)

    box_acceptance_status: str = Field(default="Pending")
    primer_acceptance_status: str = Field(default="Pending")
    acceptance_status: str = Field(default="Pending")

    start_time: Optional[datetime.datetime] = Field(default=None)
    end_time: Optional[datetime.datetime] = Field(default=None)

    # Properties for interchangeable primer / fuze terminology across codebase
    @property
    def fuze_inspection_status(self) -> str:
        return self.primer_inspection_status

    @fuze_inspection_status.setter
    def fuze_inspection_status(self, val: str):
        self.primer_inspection_status = val

    @property
    def fuze_acceptance_status(self) -> str:
        return self.primer_acceptance_status

    @fuze_acceptance_status.setter
    def fuze_acceptance_status(self, val: str):
        self.primer_acceptance_status = val

    @property
    def number_of_fuze(self) -> Optional[int]:
        return self.number_of_primer

    @number_of_fuze.setter
    def number_of_fuze(self, val: Optional[int]):
        self.number_of_primer = val

    @property
    def number_of_fuze_to_inspect(self) -> Optional[int]:
        return self.number_of_primer_to_inspect

    @number_of_fuze_to_inspect.setter
    def number_of_fuze_to_inspect(self, val: Optional[int]):
        self.number_of_primer_to_inspect = val

    @property
    def fuze_type(self) -> Optional[str]:
        return self.primer_type

    @fuze_type.setter
    def fuze_type(self, val: Optional[str]):
        self.primer_type = val

    @property
    def fuze_current_sequence(self) -> Optional[int]:
        return self.primer_current_sequence

    @fuze_current_sequence.setter
    def fuze_current_sequence(self, val: Optional[int]):
        self.primer_current_sequence = val

    @property
    def fuze_count_confirmation(self) -> Optional[int]:
        return self.primer_count_confirmation

    @fuze_count_confirmation.setter
    def fuze_count_confirmation(self, val: Optional[int]):
        self.primer_count_confirmation = val