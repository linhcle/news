import app_news as st
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import pdfminer.high_level as pdfminer

# Load the CUAD model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("akdeniz27/roberta-large-cuad")
model = AutoModelForQuestionAnswering.from_pretrained("akdeniz27/roberta-large-cuad")

def extract_relevant_clauses(text, question):
    inputs = tokenizer(question, text, return_tensors="pt", truncation=True)
    outputs = model(**inputs)
    answer_start = outputs.start_logits.argmax()
    answer_end = outputs.end_logits.argmax() + 1
    return tokenizer.decode(inputs["input_ids"][0][answer_start:answer_end])

st.title("Contract Clause Extractor")

# File upload interface
uploaded_file = st.file_uploader("Upload a contract", type=["pdf"])

if uploaded_file is not None:
    # Extract text from uploaded PDF
    text = pdfminer.extract_text(uploaded_file)
    st.write("Extracted Text Preview:")
    st.text(text[:500])  # Show a preview of the text

    # Extract important clauses
    if st.button("Extract Clauses"):
        clauses = {
        "Document Name": extract_relevant_clauses(text, "What is the name of the contract?"),
        "Parties": extract_relevant_clauses(text, "Who are the parties involved in the contract?"),
        "Agreement Date": extract_relevant_clauses(text, "What is the date of the contract?"),
        "Effective Date": extract_relevant_clauses(text, "On what date is the contract effective?"),
        "Expiration Date": extract_relevant_clauses(text, "On what date will the contract expire?"),
        "Renewal Term": extract_relevant_clauses(text, "What is the renewal term after the initial term expires?"),
        "Notice to Terminate Renewal": extract_relevant_clauses(text, "What notice period is required to terminate renewal?"),
        "Governing Law": extract_relevant_clauses(text, "Which state's law governs the interpretation of the contract?"),
        "Most Favored Nation": extract_relevant_clauses(text, "Is there a most favored nation clause?"),
        "Non-Compete": extract_relevant_clauses(text, "Is there a restriction on a party's ability to compete?"),
        "Exclusivity": extract_relevant_clauses(text, "Is there an exclusivity obligation in the contract?"),
        "No-Solicit of Customers": extract_relevant_clauses(text, "Is there a restriction on soliciting customers?"),
        "Competitive Restriction Exception": extract_relevant_clauses(text, "Are there exceptions to non-compete or exclusivity?"),
        "No-Solicit of Employees": extract_relevant_clauses(text, "Is there a restriction on hiring counterparty's employees?"),
        "Non-Disparagement": extract_relevant_clauses(text, "Is there a non-disparagement clause?"),
        "Termination for Convenience": extract_relevant_clauses(text, "Can the contract be terminated without cause?"),
        "ROFR/ROFO/ROFN": extract_relevant_clauses(text, "Does the contract provide a right of first refusal or offer?"),
        "Change of Control": extract_relevant_clauses(text, "Is there a clause for change of control events?"),
        "Anti-Assignment": extract_relevant_clauses(text, "Does the contract require consent for assignment?"),
        "Revenue/Profit Sharing": extract_relevant_clauses(text, "Is there a revenue-sharing clause?"),
        "Price Restriction": extract_relevant_clauses(text, "Are there restrictions on price changes?"),
        "Minimum Commitment": extract_relevant_clauses(text, "Is there a minimum purchase commitment?"),
        "Volume Restriction": extract_relevant_clauses(text, "Is there a volume restriction clause?"),
        "IP Ownership Assignment": extract_relevant_clauses(text, "Does one party own the intellectual property created?"),
        "Joint IP Ownership": extract_relevant_clauses(text, "Is there a clause for joint IP ownership?"),
    }
        st.write("Extracted Clauses:")
        st.json(clauses)
