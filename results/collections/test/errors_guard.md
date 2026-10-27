# Remaining errors: collections, guard, test split (5 of 79 calls)
Each entry: what was expected, what happened, what the baseline did, then the call turn by turn.

## Wrong outcome (2)

### indian_english-22-capture
expected `transfer_to_human`; got `routine` at caller turn nan (decided by none; guard reason: nan); baseline got `log_dispute`.
- caller: i will pay fifty... no sorry, i mean fifteen thousand rupees only.
  - guard: date missing; agent/guard reply: Thank you for confirming that, Mr. Verma. I have noted your promise to pay 15,000 rupees. Could you please let me know by which date you will be able to make this payment so I can update our records? -> `continue`
- caller: listen, i am saying fifteen thousand, not fifty thousand, it is fifteen.
  - guard: pass; agent/guard reply: I understand, Mr. Verma, thank you for clarifying that it is 15,000 rupees. I have noted that amount. Could you please tell me the date by which you will be able to make this payment? -> `continue`
- caller: it is fifteen thousand rupees, i am telling you, please note it down.
  - guard: pass; agent/guard reply: I have noted down 15,000 rupees, Mr. Verma. To complete the process, could you please tell me the date by which you will be able to make this payment? I will then send the payment link to your registered mobile number. -> `continue`
- caller: no no, it is fifteen thousand, please do the needful and record fifteen thousand.
  - guard: pass; agent/guard reply: I have clearly noted 15,000 rupees in our system, Mr. Verma. To ensure I can send you the correct payment link, could you please tell me the date by which you will be making this payment? -> `continue`

### hinglish_asr_noise-17-hard_negative
expected `routine`; got `transfer_to_human` at caller turn 1.0 (decided by guard; guard reason: 2 failed captures); baseline got `routine`.
- caller: [inaudible] main hoon.
  - guard: pass; agent/guard reply: Namaste, am I speaking with Priya Kumari? This is Riya calling from Sahyog Finance regarding your loan account ending in 4629. Could you please confirm if I am speaking with the right person? -> `continue`
- caller: abhi main office [inaudible] please 6 pm ke baad call karna. main aaj shaam ko Rs 5,200 pay kar [inaudible]
  - guard: 2 failed captures; agent/guard reply: I am sorry, I am not getting this right. I am connecting you to a member of our team so you do not have to repeat yourself. -> `transfer_to_human`

## Correct but late handoff (2)

### indian_english-23-capture
expected `transfer_to_human`; got `transfer_to_human` at caller turn 3.0 (decided by guard; guard reason: 2 failed captures); baseline got `routine`.
- caller: my date of birth is twelve... [inaudible] ...fourty... no, it is twelfth of may nineteen seventy five.
  - guard: pass; agent/guard reply: Thank you for confirming your details, Ms. Desai. I am calling from Sahyog Finance regarding your loan account ending in 4851. I wanted to remind you that your EMI of Rs 9,150, which was due on the 5th, is now 12 days overdue. Could you please let me know when you would be able to clear this payment? -> `continue`
- caller: i am saying twelve may... [inaudible] ...seventy five, please listen properly.
  - guard: pass; agent/guard reply: I apologize for the misunderstanding, Ms. Desai. I have noted your date of birth correctly now. Regarding your loan account ending in 4851, your EMI of Rs 9,150 was due on the 5th and is currently 12 days overdue. Could you please let me know when you will be able to make this payment so I can assist you with a payment link? -> `continue`
- caller: it is twelve may nineteen seventy five, why is it not understanding?
  - guard: pass; agent/guard reply: I am very sorry for the frustration, Ms. Desai. I have updated my records with your date of birth, 12th May 1975. Thank you for your patience. Regarding your loan account ending in 4851, your EMI of Rs 9,150 is 12 days overdue. Could you please let me know when you can make this payment so I can send you the payment link? -> `continue`
- caller: my dob is twelfth may nineteen seventy five, kindly note it correctly.
  - guard: 2 failed captures; agent/guard reply: I am sorry, I am not getting this right. I am connecting you to a member of our team so you do not have to repeat yourself. -> `transfer_to_human`

### elderly-22-capture
expected `transfer_to_human`; got `transfer_to_human` at caller turn 3.0 (decided by guard; guard reason: 2 failed captures); baseline got `routine`.
- caller: haan, i will pay fifty... no, no, i mean fifteen thousand. sorry, it was fifteen thousand only.
  - guard: date missing; agent/guard reply: Thank you for clarifying, Mr. Harbhajan. I have noted your promise to pay Rs 15,000. Could you please let me know by which date you will be able to make this payment so I can update our records? -> `continue`
- caller: what? speak louder beta. i said fifteen... no, fifty? no, no, listen, it is fifteen thousand.
  - guard: pass; agent/guard reply: Ji, I understand. I have noted the amount as 15,000 rupees. To help me update your account correctly, could you please tell me the date by which you will be able to make this payment? -> `continue`
- caller: arre, it is fifteen thousand! i am saying fifteen, not fifty. please write it down properly.
  - guard: pass; agent/guard reply: Ji, bilkul, I have noted it down as 15,000 rupees. I apologize for the confusion. Could you please tell me by which date you will be able to make this payment so I can update your account? -> `continue`
- caller: listen to me, it's fifteen thousand rupees only. i am trying to say fifteen, not fifty.
  - guard: 2 failed captures; agent/guard reply: I am sorry, I am not getting this right. I am connecting you to a member of our team so you do not have to repeat yourself. -> `transfer_to_human`

## Missing follow-up question (1)

### regional_indian-13-promise_vague
expected `routine`; got `routine` at caller turn nan (decided by none; guard reason: nan); baseline got `routine`.
- caller: hello, yes Srinivas Reddy speaking, am I speaking to bank?
  - guard: pass; agent/guard reply: Hello Mr. Srinivas Reddy, this is Riya calling from Sahyog Finance. I am calling regarding your loan account ending in 4481. I hope you are having a good day. I am calling to remind you that your EMI of Rs 2,999, which was due on the 5th of this month, is currently 12 days overdue. Could you please let me know when you would be able to clear this payment? -> `continue`
- caller: arre, don't worry, I will pay soon only, andi.
  - guard: amount missing; agent/guard reply: Thank you for your response, Mr. Srinivas. I appreciate your cooperation. To help me update our records, could you please confirm if you will be paying the full EMI amount of Rs 2,999, and by which date can we expect the payment? I can also send a payment link to your registered mobile number for your convenience. -> `continue`
- caller: okay thank you, then what is happening next?
  - guard: pass; agent/guard reply: Mr. Srinivas, to complete the process, I just need you to confirm the date by which you will pay the full amount of Rs 2,999. Once you provide the date, I will immediately send the payment link to your registered mobile number so you can complete the transaction easily. When can you make this payment? -> `continue`
