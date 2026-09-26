from abc import ABC, abstractmethod
from typing import BinaryIO
import pandas as pd


class BaseExtractor(ABC):
    """Abstract Base Class for bank-specific CSV extractors."""

    @abstractmethod
    def parse(self, file_stream: BinaryIO) -> pd.DataFrame:
        """Reads a raw CSV file stream and returns a standardized pandas DataFrame with columns:
        ['posted_date', 'description', 'amount']
        """
        pass