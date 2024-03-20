# from unittest.mock import patch
# from tests.common import (
#     TransactionCase,  #  test methods are run in a sub-transaction managed by a savepoint. The transaction’s cursor is always closed without committing.
#     SingleTransactionCase,  # test methods are run in the same transaction
#     HttpCase,  # Transactional HTTP TestCase with url_open and Chrome headless helpers
#     Form,  # Server-side form view implementation (partial)
#     tagged,
# )
# from .common import marco_importerTestCommon
#
#
# class marco_importerTestFoo(marco_importerTestCommon):
#     pass