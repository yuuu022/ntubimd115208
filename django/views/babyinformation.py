"""
views/babyinformation.py

【轉接檔】urls.py 指向此模組，實際邏輯已拆分至：

    views/baby_utils.py      — 所有 helper 函式
    views/baby_dashboard.py  — 主頁總覽 baby()
    views/baby_info.py       — add_baby_information(), edit_baby_information()
    views/baby_record.py     — add_baby_record(), edit_baby_record(), delete_baby_record()

core/urls.py 不需修改，所有 import 從此處轉發。
"""

from views.baby_dashboard import baby                                    # noqa: F401
from views.baby_info import add_baby_information, edit_baby_information  # noqa: F401
from views.baby_record import (                                          # noqa: F401
    add_baby_record,
    edit_baby_record,
    delete_baby_record,
)
