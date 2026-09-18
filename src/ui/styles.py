"""
Module Cấu hình Giao diện & Phong cách Trực quan (UI Styles & Plotly Config)
Cung cấp bảng mã CSS hiện đại, tối ưu giao diện Dark mode và cấu hình Plotly mượt mà chống rung giật.
"""
import streamlit as st

# Cấu hình tương tác biểu đồ chuyên nghiệp (Lăn chuột mượt mà, chống rung giật)
PLOTLY_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "doubleClick": "reset",
    "showTips": False,
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "chart_export",
        "height": 800,
        "width": 1200,
        "scale": 2,
    },
}

CUSTOM_CSS = """
<style>
    /* Chống rung giật trang web khi lăn chuột zoom trên biểu đồ */
    .stPlotlyChart {
        overscroll-behavior: contain !important;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .kpi-title {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
    }
    .price-up { color: #10b981 !important; font-weight: 700; }
    .price-down { color: #ef4444 !important; font-weight: 700; }
    .price-ref { color: #f59e0b !important; font-weight: 700; }
    .stAlert { border-radius: 8px; }
</style>
"""


def apply_custom_styles():
    """Áp dụng các style CSS tùy chỉnh vào ứng dụng Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
