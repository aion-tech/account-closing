import logging
import inspect

_logger = logging.getLogger(__name__)

def _progress_logger(iterator: int, all_records: list, additional_info: str = ""):
    # Ottieni il nome della funzione chiamante
    caller_function = inspect.stack()[1].function

    _logger.warning(
        f"Called from: {caller_function} | <--- {str(iterator+1)} | {str(len(all_records))} ---> {additional_info}"
    )
