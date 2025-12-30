import streamlit as st


def inject_global_styles():
    st.markdown(
        """
        <style>
        /* Make headers and metrics more compact */
        .stHeader {
            margin-top: 6px;
            margin-bottom: 4px;
        }
        .metric-label {
            font-size: 14px;
        }
        .small-muted { color: #666; font-size:12px }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_menu(options, key="sidebar_page"):
    """Render a clean sidebar menu and return selected option."""
    st.sidebar.title("📋 เมนู")
    return st.sidebar.radio("", options, key=key)


def render_header(title: str, subtitle: str = None):
    col1, col2 = st.columns([4,1])
    with col1:
        st.markdown(f"<h1 style='margin-bottom:0.1rem'>{title}</h1>", unsafe_allow_html=True)
        if subtitle:
            st.markdown(f"<div class='small-muted'>{subtitle}</div>", unsafe_allow_html=True)
    with col2:
        logo_path = "static/images/logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=64)
