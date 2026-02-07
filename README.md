# SmartSacco AI Agent
<img width="1919" height="759" alt="image" src="https://github.com/user-attachments/assets/7b882fa6-3025-4f4c-b2de-4a7243f56298" />


## What
- An AI agent/LLM that predicts whether a member of a given SACCO is likely to default on a loan based on previous loan history, credit score, and investment amounts.

## How to run SmartSacco
#### Prerequisites
- Python 3.10+

#### steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Mikitoxo/smartsaccoai.git
   ```
2. Run the Streamlit app: 
   ```bash
   streamlit run app.py
   ```
3. Enter a member Id value between ***1-1000*** or name to search e.g., Kwame 
4. Enter the requested loan amount
5. Press the 'analyze' button to receive an output from the agent.
6. Whether accepted or rejected, click the 'open in email app' button to send a message to the Sacco Member informing them of the decision and the reasoning if the request has been rejected.
   <img width="1298" height="583" alt="image" src="https://github.com/user-attachments/assets/679372f1-c4f5-4741-9066-9731ddb04354" />

## How it works
- Input: User logs in and submits member_id of the Sacco member and amount they want to borrow.
- Search: Queries the dataset for member data.
- LLM Analysis: smartsacco_brain_v2.pkl (the model) evaluates eligibility.
- Output: Based on the member data, the AI agent predicts whether or not the member is eligible for the loan, it also states why they are/are not eligible and provides a ready-to-send email template for easy communication.
- sample response:
  <img width="1337" height="460" alt="image" src="https://github.com/user-attachments/assets/0c2780ed-b6dd-40a3-935f-840978b9f0ca" />
  <img width="1316" height="232" alt="image" src="https://github.com/user-attachments/assets/6f574c1a-cd75-4328-8304-89ba90411e1f" />

  
