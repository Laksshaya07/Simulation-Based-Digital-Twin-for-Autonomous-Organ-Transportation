import streamlit as st
import logging

logger = logging.getLogger("OrganDroneApp.Navigation")

def safe_rerun():
    """
    Safely trigger a Streamlit rerun, catching issues where the client
    has disconnected from the server and cannot receive the rerun backMessage.
    """
    try:
        st.rerun()
    except BaseException as e:
        err_msg = str(e)
        if "Cannot send rerun backMessage" in err_msg or "disconnected from server" in err_msg:
            logger.info("Ignored Streamlit rerun exception because client is disconnected.")
        else:
            raise
