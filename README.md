# SmartSacco AI Agent
<img width="1919" height="676" alt="image" src="https://github.com/user-attachments/assets/bdfa6ab6-60c6-4d93-80f7-06f24674b9be" />

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
   <img width="1305" height="577" alt="image" src="https://github.com/user-attachments/assets/adb8cef9-00d1-44da-baae-1506d13204fc" />



## How it works
- Input: User logs in and submits member_id of the Sacco member and amount they want to borrow.
- Search: Queries the dataset for member data.
- LLM Analysis: smartsacco_brain_v2.pkl (the model) evaluates eligibility.
- Output: Based on the member data, the AI agent predicts whether or not the member is eligible for the loan, it also states why they are/are not eligible and provides a ready-to-send email template for easy communication.
- sample response:
  <img width="866" height="356" alt="image" src="https://github.com/user-attachments/assets/d78b50fc-b950-4455-b6d9-76a39aa0957e" />
  <img width="689" height="172" alt="image" src="https://github.com/user-attachments/assets/1b4adeda-ee71-4d1f-8883-902240365b8d" />
