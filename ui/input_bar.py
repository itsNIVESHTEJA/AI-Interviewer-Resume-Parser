"""
Answer input bar (text + mic + submit/skip/end).
Kept as a separate module for structure parity with the original project.
The actual implementation lives inline in ui/chat_view.py::render_chat_view
because Streamlit's form/session-state flow is simplest kept together with
the surrounding chat rendering logic. Import this module if you want to
factor the input bar out further.
"""
