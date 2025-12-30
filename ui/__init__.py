"""UI helpers for Streamlit app - placeholder for components and styles."""

__all__ = ["render_header"]


def render_header(title: str):
    import streamlit as st
    st.title(title)
    st.markdown("---")
