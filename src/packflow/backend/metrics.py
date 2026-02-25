from typing import Optional

from pydantic import BaseModel, model_validator


class ExecutionTimes(BaseModel):
    preprocess: float
    transform_inputs: Optional[float] = None
    execute: float
    transform_outputs: Optional[float] = None

    def total(self):
        """
        Return the total execution time based on the sum of each defined field
        """
        return sum([getattr(self, field) for field in self.model_fields_set])


class ExecutionMetrics(BaseModel):
    batch_size: int
    execution_times: ExecutionTimes
    total_execution_time: float = None

    @model_validator(mode="after")
    def calculate_total_execution_time(self):
        self.total_execution_time = self.execution_times.total()
        return self
