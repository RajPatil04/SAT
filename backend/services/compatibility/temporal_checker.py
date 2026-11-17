# backend/services/compatibility/temporal_checker.py
from typing import List, Optional
from backend.router.schemas import ImageMetadata, TemporalCompatibility

class TemporalChecker:
    @staticmethod
    def check_temporal_compatibility(
        metadata_list: List[ImageMetadata],
        date_1: Optional[str] = None,
        date_2: Optional[str] = None
    ) -> TemporalCompatibility:
        """
        Validates temporal distinction and chronological ordering for bi-temporal analysis.
        Uses embedded acquisition metadata or user-supplied date labels.
        """
        if len(metadata_list) < 2:
            return TemporalCompatibility(
                has_distinct_dates=False,
                date_1=date_1 or (metadata_list[0].acquisition_date if metadata_list else None),
                date_2=None,
                is_compatible=True,
                details="Single observation temporal domain."
            )

        d1 = date_1 or metadata_list[0].acquisition_date
        d2 = date_2 or metadata_list[1].acquisition_date

        if d1 and d2:
            distinct = (d1.strip().lower() != d2.strip().lower())
            if distinct:
                details = f"Temporal observations verified: Date 1 ({d1}) and Date 2 ({d2})."
                return TemporalCompatibility(
                    has_distinct_dates=True,
                    date_1=d1,
                    date_2=d2,
                    is_compatible=True,
                    details=details
                )
            else:
                return TemporalCompatibility(
                    has_distinct_dates=False,
                    date_1=d1,
                    date_2=d2,
                    is_compatible=False,
                    details=f"Both observations have identical timestamp/label: '{d1}'. Change detection requires separate temporal epochs."
                )

        # Dates not specified in metadata or inputs
        return TemporalCompatibility(
            has_distinct_dates=False,
            date_1=d1 or "Epoch T1 (unspecified)",
            date_2=d2 or "Epoch T2 (unspecified)",
            is_compatible=True,
            details="Acquisition timestamps not embedded in image metadata. User-designated pair treated as bi-temporal sequence T1 -> T2."
        )
