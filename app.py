import streamlit as st
import json
import random
import csv
import io
import os
from datetime import date
from drive import load_flashcards, save_flashcards

# ── State init ───────────────────────────────────────────────────────────────
def load_meta():
    if os.path.exists("meta.json"):
        with open("meta.json") as f:
            return json.load(f)
    return {}

def save_meta(meta):
    with open("meta.json", "w") as f:
        json.dump(meta, f, indent=2)

if "all_decks" not in st.session_state:
    st.session_state.all_decks = load_flashcards()
if "meta" not in st.session_state:
    st.session_state.meta = load_meta()

all_decks: dict = st.session_state.all_decks
meta: dict = st.session_state.meta

GITHUB_BASE = "https://github.com/kimngkq/esp-flashcards/blob/main/flashcards.json"

# ── Bulk parse helper ─────────────────────────────────────────────────────────
def parse_upload(file) -> list[dict]:
    filename = file.name.lower()
    content = file.read().decode("utf-8", errors="ignore")
    cards = []
    if filename.endswith(".csv"):
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if len(row) >= 2:
                q, a = row[0].strip(), row[1].strip()
                if q and a:
                    cards.append({"question": q, "answer": a})
    else:
        for line in content.splitlines():
            if ":" in line:
                parts = line.split(":", 1)
                q, a = parts[0].strip(), parts[1].strip()
                if q and a:
                    cards.append({"question": q, "answer": a})
    return cards

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Flashcards", page_icon="🃏")
st.title("🃏 Flashcards")

tab1, tab2, tab3 = st.tabs(["Create", "Study", "Edit"])

# ── CREATE ────────────────────────────────────────────────────────────────────
with tab1:
    st.header("Create a new deck")
    deck_name = st.text_input("Deck name", placeholder="e.g. Spanish Verbs")
    input_method = st.radio("How do you want to add cards?", ["Type manually", "Upload file"])

    if input_method == "Type manually":
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

        if st.button("➕ Add another card"):
            st.session_state.cards_input.append({"question": "", "answer": ""})
            st.rerun()

        if st.button("💾 Save deck", disabled=not deck_name):
            valid_cards = [c for c in st.session_state.cards_input if c["question"] and c["answer"]]
            if not valid_cards:
                st.warning("Please add at least one card with a question and answer.")
            else:
                all_decks[deck_name] = valid_cards
                save_flashcards(all_decks)
                st.success(f"Saved {len(valid_cards)} cards!")
                st.session_state.cards_input = [{"question": "", "answer": ""}]
                st.rerun()

    else:
        st.subheader("Upload a file")
        st.markdown("""
**Accepted formats:**
- **CSV** — two columns, no header needed: `question, answer`
- **Text file (.txt)** — one card per line: `question : answer`
        """)

        st.download_button(
            "⬇️ Download CSV template",
            data="question,answer\nWhat is the capital of France?,Paris\nWhat is 2+2?,4\n",
            file_name="flashcard_template.csv",
            mime="text/csv"
        )

        uploaded = st.file_uploader("Upload your file", type=["csv", "txt"])

        if uploaded:
            parsed = parse_upload(uploaded)
            if not parsed:
                st.error("Couldn't find any cards in that file. Make sure it matches the format above.")
            else:
                # Store parsed cards in session state so they survive reruns
                st.session_state["parsed_upload"] = parsed

        if "parsed_upload" in st.session_state:
            parsed = st.session_state["parsed_upload"]
            st.success(f"Found {len(parsed)} cards — preview:")
            for i, card in enumerate(parsed[:5]):
                st.markdown(f"**{i+1}.** {card['question']} → {card['answer']}")
            if len(parsed) > 5:
                st.caption(f"... and {len(parsed) - 5} more")

            if st.button("💾 Save deck", disabled=not deck_name, key="save_upload"):
                all_decks[deck_name] = parsed
                save_flashcards(all_decks)
                st.success(f"Saved {len(parsed)} cards to '{deck_name}'!")
                del st.session_state["parsed_upload"]
                st.rerun()

# ── STUDY ─────────────────────────────────────────────────────────────────────
with tab2:
    st.header("Study")
    if not all_decks:
        st.info("No decks yet — create some first!")
    else:
        for name in all_decks:
            last = meta.get(name, {}).get("last_reviewed", "Never")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}** · {len(all_decks[name])} cards · Last reviewed: {last} · [view file]({GITHUB_BASE})")
            with col2:
                if st.button("Study", key=f"study_{name}"):
                    st.session_state["study_cards"] = list(all_decks[name])
                    st.session_state["study_deck"] = name
                    st.session_state["idx"] = 0
                    st.session_state["show"] = False
                    meta.setdefault(name, {})["last_reviewed"] = str(date.today())
                    save_meta(meta)
                    st.rerun()

        if "study_cards" in st.session_state:
            st.divider()
            cards = st.session_state["study_cards"]
            idx = st.session_state["idx"]
            deck = st.session_state["study_deck"]

            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Studying: {deck}")
            with col2:
                if st.button("🔀 Scramble"):
                    random.shuffle(st.session_state["study_cards"])
                    st.session_state["idx"] = 0
                    st.session_state["show"] = False
                    st.rerun()

            st.progress((idx + 1) / len(cards), text=f"Card {idx + 1} of {len(cards)}")
            st.markdown(f"### ❓ {cards[idx]['question']}")

            # Single button that toggles between Show Answer and Next
            if not st.session_state.get("show"):
                if st.button("👁 Show Answer", use_container_width=True):
                    st.session_state["show"] = True
                    st.rerun()
            else:
                st.success(cards[idx]["answer"])
                if idx < len(cards) - 1:
                    if st.button("Next ➡", use_container_width=True):
                        st.session_state["idx"] += 1
                        st.session_state["show"] = False
                        st.rerun()
                else:
                    st.info("🎉 You've reached the end of the deck!")
                    if st.button("🔁 Start again", use_container_width=True):
                        st.session_state["idx"] = 0
                        st.session_state["show"] = False
                        st.rerun()

                # Keep prev button as a secondary option below
                if idx > 0:
                    if st.button("⬅ Previous", use_container_width=True):
                        st.session_state["idx"] -= 1
                        st.session_state["show"] = False
                        st.rerun()

# ── EDIT ──────────────────────────────────────────────────────────────────────
with tab3:
    st.header("Edit a deck")
    if not all_decks:
        st.info("No decks yet — create some first!")
    else:
        chosen = st.selectbox("Choose a deck to edit", list(all_decks.keys()))
        if st.button("Load deck for editing"):
            st.session_state["edit_deck"] = chosen
            st.session_state["edit_cards"] = [c.copy() for c in all_decks[chosen]]
            st.rerun()

        if "edit_deck" in st.session_state and st.session_state["edit_deck"] == chosen:
            st.subheader(f"Editing: {st.session_state['edit_deck']}")

            with st.expander("➕ Bulk add cards from file"):
                st.markdown("Upload a CSV or text file to append cards to this deck.")
                bulk_file = st.file_uploader("Upload file", type=["csv", "txt"], key="bulk_edit")
                if bulk_file:
                    bulk_parsed = parse_upload(bulk_file)
                    if not bulk_parsed:
                        st.error("Couldn't find any cards in that file.")
                    else:
                        st.session_state["bulk_parsed"] = bulk_parsed

            if "bulk_parsed" in st.session_state:
                bulk_parsed = st.session_state["bulk_parsed"]
                st.success(f"Found {len(bulk_parsed)} cards to append.")
                for i, card in enumerate(bulk_parsed[:5]):
                    st.markdown(f"**{i+1}.** {card['question']} → {card['answer']}")
                if len(bulk_parsed) > 5:
                    st.caption(f"... and {len(bulk_parsed) - 5} more")
                if st.button("Append to deck"):
                    deck_key = st.session_state["edit_deck"]
                    updated_cards = st.session_state["edit_cards"] + bulk_parsed
                    st.session_state["edit_cards"] = updated_cards
                    st.session_state.all_decks[deck_key] = updated_cards
                    save_flashcards(st.session_state.all_decks)
                    del st.session_state["bulk_parsed"]
                    st.rerun()

            for i, card in enumerate(st.session_state["edit_cards"]):
                st.markdown(f"**Card {i+1}**")
                col1, col2, col3 = st.columns([3, 3, 1])
                with col1:
                    st.session_state["edit_cards"][i]["question"] = st.text_input(
                        "Question", value=card["question"], key=f"eq_{i}"
                    )
                with col2:
                    st.session_state["edit_cards"][i]["answer"] = st.text_input(
                        "Answer", value=card["answer"], key=f"ea_{i}"
                    )
                with col3:
                    if st.button("🗑", key=f"del_{i}"):
                        st.session_state["edit_cards"].pop(i)
                        st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add card manually"):
                    st.session_state["edit_cards"].append({"question": "", "answer": ""})
                    st.rerun()
            with col2:
                if st.button("💾 Save changes"):
                    valid = [c for c in st.session_state["edit_cards"] if c["question"] and c["answer"]]
                    all_decks[st.session_state["edit_deck"]] = valid
                    save_flashcards(all_decks)
                    st.success("Deck updated!")
                    del st.session_state["edit_deck"]
                    del st.session_state["edit_cards"]
                    st.rerun()