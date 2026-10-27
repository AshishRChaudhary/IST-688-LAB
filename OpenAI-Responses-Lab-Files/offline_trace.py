# Prepared by: Sherwin Murzello and Mrgaj Iyer
"""No-key fallback activity: inspect a synthetic Responses API tool-call trace.
This does NOT call OpenAI. All messages below are simulated examples.
"""
import json
from pathlib import Path

SIMULATED_RESPONSE = {
    "id": "resp_example_001",
    "output": [{
        "type": "function_call",
        "name": "lookup_campus_faq",
        "call_id": "call_example_001",
        "arguments": json.dumps({"topic": "it_support"}),
    }],
}
print("SIMULATED first response:")
print(json.dumps(SIMULATED_RESPONSE, indent=2))
call = SIMULATED_RESPONSE["output"][0]
args = json.loads(call["arguments"])
with open(Path(__file__).with_name("campus_faq.json"), encoding="utf-8") as file:
    faq = json.load(file)
result = {"topic": args["topic"], "answer": faq[args["topic"]]}
message = {
    "type": "function_call_output",
    "call_id": call["call_id"],
    "output": json.dumps(result),
}
print("\nSIMULATED developer tool output (what your code sends next):")
print(json.dumps(message, indent=2))
print("\nDISCUSS: Why does the model not know this local FAQ answer without a tool?")
print("DISCUSS: Which field links the tool output to the model's call?")
print("DISCUSS: What would go wrong if the answer were fabricated instead?")
