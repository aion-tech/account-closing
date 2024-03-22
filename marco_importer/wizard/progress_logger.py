import logging


_logger = logging.getLogger(__name__)


def _progress_logger(iterator: int, all_records: list, additional_info: str = ""):
    _logger.warning(
        f"<--- {str(iterator+1)} | {str(len(all_records))} ---> {additional_info}"
    )