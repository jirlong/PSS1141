import streamlit as st
import os
from rag_core import RAGSystem

st.set_page_config(page_title="AI RAG Assistant", layout="wide")

def main():
    st.title("🤖 AI RAG Assistant")
    
    # Initialize RAG System
    if "rag_system" not in st.session_state:
        st.session_state.rag_system = RAGSystem()
    
    rag = st.session_state.rag_system

    # Sidebar
    with st.sidebar:
        st.header("System Control")
        
        # Status Indicator
        if rag.vector_store:
            st.success("System Ready: Index Loaded")
        else:
            st.warning("System Not Ready: No Index")

        if st.button("Re-index Database"):
            with st.spinner("Indexing documents..."):
                rag.clear_index()
                result = rag.load_and_index()
                if "Indexed" in result:
                    st.success(result)
                else:
                    st.error(result)
        
        st.divider()
        st.subheader("Documents in rag_data")
        if os.path.exists("rag_data"):
            files = [f for f in os.listdir("rag_data") if f.endswith(('.pdf', '.docx'))]
            if files:
                for f in files:
                    st.text(f"📄 {f}")
            else:
                st.info("No documents found.")
        else:
            st.error("rag_data folder missing.")

    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = rag.query(prompt)
                answer = response["answer"]
                sources = response["sources"]
                
                st.markdown(answer)
                if sources:
                    st.markdown(f"**Sources:** {', '.join(sources)}")
                
                full_response = answer
                if sources:
                    full_response += f"\n\n**Sources:** {', '.join(sources)}"
                st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
