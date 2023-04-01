# 'primary' 颜色对应 theme.py 中的 primary_hue
# 'secondary' 颜色对应 theme.py 中的 neutral_hue
# 'stop' 颜色对应 theme.py 中的 color_er
# 默认按钮颜色是 secondary
from toolbox import clear_line_break
from functions.batch_summary_pdfs import batch_summary_pdfs

def get_functionals():
    return {
        "summary生成": {
            "Color":    r"secondary",
            "Function": batch_summary_pdfs
        },
    }
