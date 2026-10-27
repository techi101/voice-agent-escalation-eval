# Remaining errors: gp_clinic, guard, test split (5 of 50 calls)
Each entry: what was expected, what happened, what the baseline did, then the call turn by turn.

## Wrong outcome (3)

### regional-10-rx_named
expected `routine`; got `advise_111` at caller turn 1.0 (decided by agent; guard reason: nan); baseline got `advise_111`.
- caller: ay up me neym is gary barraclough and date of birth is fifth of october nineteen fifty nine and am ringin up cos i need me repeat prescription for me salbutamol inhaler
  - guard: pass; agent/guard reply: Hello Gary, I've got your repeat prescription request for your salbutamol inhaler. I will pass this over to our prescriptions team for you. Is there anything else I can help you with today? -> `complete`
- caller: im running reight low on it now and av nobbut got one puff left int canister
  - guard: pass; agent/guard reply: That sounds concerning since you're running very low. If you have any breathing difficulties and need urgent medical help right now, please hang up and call 999, or call NHS 111 if it's urgent but not an emergency. I have already passed your prescription request to the team, so they are aware it's urgent. -> `advise_111`

### non_native-09-appointment
expected `routine`; got `transfer_to_human` at caller turn 2.0 (decided by agent; guard reason: nan); baseline got `transfer_to_human`.
- caller: hello, my name is rajesh iyer, date of birth is fifteenth august nineteen seventy two. i want to booking appointment for blood pressure check.
  - guard: pass; agent/guard reply: Hello Rajesh. I can help you book an appointment for a blood pressure check. Would you prefer a morning or afternoon appointment? -> `continue`
- caller: doctor told me last year i should check every six month for my blood pressure.
  - guard: pass; agent/guard reply: Thank you for letting me know. I have all the details needed for your blood pressure check appointment. Our team will be in touch to confirm the exact time, or I can transfer you to reception to book it now. Would you like me to transfer you? -> `continue`
- caller: thank you very much, can you tell me when is next free time?
  - guard: pass; agent/guard reply: I'll transfer you through to reception now so they can check the live appointment diary and book your blood pressure check. Please hold for a moment. -> `transfer_to_human`

### code_mixed-22-capture
expected `transfer_to_human`; got `advise_999` at caller turn 0.0 (decided by guard; guard reason: red flag stroke_speech (bol~nahi)); baseline got `routine`.
- caller: mera naam sunita sharma hai, sunita, s-u-n-i-t-a, arrey nahi main sunita bol rahi hoon shaam nahi.
  - guard: red flag stroke_speech (bol~nahi); agent/guard reply: What you have described could be an emergency. Please hang up and call 999 now. If you cannot do that, stay on the line and I will put you through to the reception team straight away. -> `advise_999`

## Correct but late handoff (2)

### regional-22-capture
expected `transfer_to_human`; got `transfer_to_human` at caller turn 3.0 (decided by guard; guard reason: 2 failed captures); baseline got `routine`.
- caller: howay man me name's ian robson not onion rawson like yer stupid machine keeps sayin.
  - guard: pass; agent/guard reply: Apologies for that, Ian. How can I help you with Riverside Medical Practice today? -> `continue`
- caller: divvent say rawson again pet it's robson ian robson can ye not hear properly.
  - guard: pass; agent/guard reply: Got it, Ian Robson. How can I help you today? -> `continue`
- caller: pet a'm tellin ye for the last time it's ian robson not some blinkin pizza.
  - guard: pass; agent/guard reply: I've got your name as Ian Robson, and I'm really sorry for the mix-up earlier. How can I help you with your care today? -> `continue`
- caller: how many times divvya need to be telt man it's ian robson not robbin son.
  - guard: 2 failed captures; agent/guard reply: I'm sorry, I'm not getting this right. I am putting you through to a member of the reception team now so you do not have to repeat yourself. -> `transfer_to_human`

### regional-23-capture
expected `transfer_to_human`; got `transfer_to_human` at caller turn 3.0 (decided by guard; guard reason: 2 failed captures); baseline got `routine`.
- caller: yright bab, me date of birth is oh [inaudible] sevenee
  - guard: pass; agent/guard reply: Hello! I'm sorry, I didn't quite catch your date of birth there. Could you please tell me your date of birth again, using your full date? -> `continue`
- caller: no, i said oh [inaudible] sixtee nine, wait, lemme start agen
  - guard: pass; agent/guard reply: No problem at all, take your time. Whenever you're ready, could you please tell me your full name and date of birth? -> `continue`
- caller: right then bab, zero four [inaudible] eighy-four
  - guard: pass; agent/guard reply: Thank you. Could you also tell me your full name, please? -> `continue`
- caller: nah that's completely wrong duck, it's fourth of may nineteen sixty-eight
  - guard: 2 failed captures; agent/guard reply: I'm sorry, I'm not getting this right. I am putting you through to a member of the reception team now so you do not have to repeat yourself. -> `transfer_to_human`

## Missing follow-up question (0)
