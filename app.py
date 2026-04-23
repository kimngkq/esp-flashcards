import streamlit as st
import json
from drive import load_flashcards, save_flashcards

if "all_decks" not in st.session_state:
    st.session_state.all_decks = load_flashcards()

all_decks: dict = st.session_state.all_decks

st.set_page_config(page_title="Flashcards", page_icon="🃏")
st.title("🃏 Flashcards")

tab1, tab2 = st.tabs(["Create", "Study"])

with tab1:
    st.header("Create a new deck")
    deck_name = st.text_input("Deck name", placeholder="e.g. Spanish Verbs")

    st.subheader("Add cards")
    if "cards_input" not in st.session_state:
        st.session_state.cards_input = [{"question": "", "answer": ""}]

    for i, card in enumerate(st.session_state.cards_input):
        st.markdown(f"**Card {i+1}**")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.cards_input[i]["question"] = st.text_input(
                "Question", value=card["question"], key=f"q_{i}"
            )
        with col2:
            st.session_state.cards_input[i]["answer"] = st.text_input(
                "Answer", value=card["answer"], key=f"a_{i}"
            )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add another card"):
            st.session_state.cards_input.append({"question": "", "answer": ""})
            st.rerun()
    with col2:
        if st.button("💾 Save deck to Google Drive", disabled=not deck_name):
            valid_cards = [c for c in st.session_state.cards_input if c["question"] and c["answer"]]
            if not valid_cards:
                st.warning("Please add at least one card with a question and answer.")
            else:
                all_decks[deck_name] = valid_cards
                save_flashcards(all_decks)
                st.success(f"Saved {len(valid_cards)} cards to Google Drive!")
                st.session_state.cards_input = [{"question": "", "answer": ""}]
                st.rerun()

with tab2:
    st.header("Study")
    if not all_decks:
        st.info("No decks yet — create some first!")
    else:
        chosen = st.selectbox("Choose a deck", list(all_decks.keys()))
        if st.button("Load"):
            st.session_state["study_cards"] = all_decks[chosen]
            st.session_state["idx"] = 0
            st.session_state["show"] = False

        if "study_cards" in st.session_state:
            cards = st.session_state["study_cards"]
            idx = st.session_state["idx"]
            st.progress((idx + 1) / len(cards), text=f"Card {idx + 1} of {len(cards)}")
            st.markdown(f"### ❓ {cards[idx]['question']}")

            if st.button("Show Answer"):
                st.session_state["show"] = True
            if st.session_state.get("show"):
                st.success(cards[idx]["answer"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⬅ Prev") and idx > 0:
                        st.session_state["idx"] -= 1
                        st.session_state["show"] = False
                        st.rerun()
                with col2:
                    if st.button("Next ➡") and idx < len(cards) - 1:
                        st.session_state["idx"] += 1
                        st.session_state["show"] = False
                        st.rerun()
                        