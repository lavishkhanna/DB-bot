import streamlit as st
import pandas as pd
from datetime import datetime
import time

from config import API_BASE_URL, APP_TITLE, APP_ICON, PAGE_TITLE
from api_client import APIClient
from utils import (
    format_table_data, 
    format_sql_for_display, 
    get_sample_questions,
    export_to_csv
)

# Page config
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .sql-box {
        background-color: #263238;
        color: #aed581;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize API client
@st.cache_resource
def get_api_client():
    return APIClient(API_BASE_URL)

api_client = get_api_client()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Backend health check
    st.subheader("Backend Status")
    health = api_client.health_check()
    
    if health.get("status") == "healthy":
        st.success("✅ Connected")
        st.caption(f"Database: {health.get('database', 'Unknown')}")
    else:
        st.error("❌ Backend Unavailable")
        st.caption(f"Error: {health.get('error', 'Unknown')}")
    
    st.divider()
    
    # Sample questions
    st.subheader("💡 Sample Questions")
    sample_questions = get_sample_questions()
    
    for question in sample_questions:
        if st.button(question, key=f"sample_{question}", use_container_width=True):
            st.session_state.selected_question = question
    
    st.divider()
    
    # Database schema viewer
    if st.button("📊 View Database Schema", use_container_width=True):
        with st.spinner("Loading schema..."):
            schema = api_client.get_schema()
            if schema:
                st.session_state.show_schema = True
                st.session_state.schema_data = schema
    
    st.divider()
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()
    
    st.divider()
    
    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Database Chatbot**
        
        Ask questions about your database in natural language.
        The AI will generate and execute SQL queries for you.
        
        **Features:**
        - Natural language queries
        - SQL generation
        - Result visualization
        - Export to CSV
        """)

# Main content
st.title(APP_TITLE)
st.caption("Ask questions about your database in natural language")

# Show schema if requested
if st.session_state.get("show_schema", False):
    with st.expander("📊 Database Schema", expanded=True):
        schema_data = st.session_state.get("schema_data", {})
        tables = schema_data.get("schema", [])
        
        if tables:
            for table in tables:
                st.subheader(f"Table: {table['table_name']}")
                
                # Create DataFrame for columns
                columns_data = []
                for col in table['columns']:
                    columns_data.append({
                        "Column": col['column_name'],
                        "Type": col['data_type'],
                        "Nullable": col['is_nullable']
                    })
                
                df = pd.DataFrame(columns_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.divider()
        else:
            st.warning("No schema data available")
    
    if st.button("Close Schema"):
        st.session_state.show_schema = False
        st.rerun()

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    role = message["role"]
    content = message["content"]

    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(content)

            # Show SQL query if available
            if "sql" in message:
                with st.expander("🔍 View SQL Query"):
                    st.code(message["sql"], language="sql")

            # Show data table if available
            if "data" in message and message["data"]:
                df = format_table_data(message["data"])

                if not df.empty:
                    st.dataframe(df, use_container_width=True)

                    # Download button
                    csv = export_to_csv(df)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"download_csv_msg_{idx}"
                    )

# Handle selected sample question
if "selected_question" in st.session_state:
    user_input = st.session_state.selected_question
    del st.session_state.selected_question
else:
    # Chat input
    user_input = st.chat_input("Ask a question about your database...")

# Process user input
if user_input:
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    
    # Get assistant response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            # Send to API
            response = api_client.send_message(
                message=user_input,
                conversation_history=st.session_state.conversation_history
            )
            
            # Display response
            assistant_message = response.get("response", "Sorry, I couldn't process that.")
            st.markdown(assistant_message)
            
            # Store for chat display
            message_data = {
                "role": "assistant",
                "content": assistant_message
            }
            
            # Show SQL if available
            if "sql_executed" in response and response["sql_executed"]:
                sql = response["sql_executed"]
                message_data["sql"] = sql
                
                with st.expander("🔍 View SQL Query"):
                    st.code(sql, language="sql")
            
            # Show data table if available
            if "data_preview" in response and response["data_preview"]:
                data = response["data_preview"]
                message_data["data"] = data
                
                df = format_table_data(data)
                
                if not df.empty:
                    row_count = response.get("row_count", len(data))
                    
                    if row_count > len(data):
                        st.info(f"Showing {len(data)} of {row_count} results")
                    
                    st.dataframe(df, use_container_width=True)

                    # Download button
                    csv = export_to_csv(df)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_csv_current"
                    )
            
            # Show error if any
            if "error" in response:
                st.error(f"⚠️ Error: {response['error']}")
            
            # Add to messages
            st.session_state.messages.append(message_data)
            
            # Update conversation history for API
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
    
    # Rerun to update UI
    st.rerun()

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔗 Backend: " + API_BASE_URL)
with col2:
    st.caption(f"💬 Messages: {len(st.session_state.messages)}")
with col3:
    st.caption("🤖 Powered by AI")