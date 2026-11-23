import streamlit as st
from modules.client_tools import render_client_studio_ferramentas

def render_converter():
    st.markdown("### ⚡ Ferramentas Rápidas no Seu Aparelho")
    render_client_studio_ferramentas(st.session_state.get("usuario_id", "user"))
