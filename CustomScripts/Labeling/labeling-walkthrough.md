# Performance Improvement Examples

We implemented the three core architectural patterns for improving model performance into separate scripts, specifically testing them against the complex mathematical edge cases that the `claude-haiku` model failed on previously.

The results provide an incredible real-world demonstration of how these patterns work!

## 1. Chain of Thought (CoT)
**Script:** [cot_extraction_example.py](file:///d:/Source/Learning/ClaudeArchitectExamples/cot_extraction_example.py)

**What we did:** We added a `scratchpad` field to the Pydantic schema, forcing Haiku to write out its math step-by-step before outputting the final revenue number.
**The Result: PERFECT SUCCESS ✅**
By forcing the model to calculate the components individually (e.g., calculating the returns, then the rebates, then subtracting them from gross), Haiku easily arrived at the correct answer (`46.5`), completely fixing its previous error. This proves that CoT is the most powerful tool for improving logic and math tasks.

## 2. Few-Shot Prompting
**Script:** [few_shot_extraction_example.py](file:///d:/Source/Learning/ClaudeArchitectExamples/few_shot_extraction_example.py)

**What we did:** We injected structural examples of how to do tiered math directly into the System Prompt.
**The Result: FAILED ❌**
Haiku still failed the extraction. *Why?* Because smaller models struggle to hold complex math in their head even when shown a pattern. Without a scratchpad to actually perform the calculation line-by-line, the model still tried to jump straight to the answer and fumbled the math. 
> [!NOTE]
> This is a critical lesson for the Anthropic Certification: Few-shot prompting helps with formatting and structural understanding, but it **cannot replace Chain of Thought** for mathematical or logic-heavy tasks.

## 3. Verification Loops (Self-Correction)
**Script:** [verification_loop_example.py](file:///d:/Source/Learning/ClaudeArchitectExamples/verification_loop_example.py)

**What we did:** We created a two-agent system. Agent A did the extraction blindly, and Agent B acted as an Auditor, explicitly checking Agent A's math.
**The Result: MIXED (1 Fixed, 1 Failed) ⚠️**
- On the first problem, Agent B successfully caught Agent A's error, did the math correctly in its scratchpad, and output the correct value (`46.25`), saving the day!
- On the second problem, Agent B caught Agent A's error, but then *Agent B also made a math error* (hallucinating that `1,000,000 - 50,000 - 200,000 = 800,000`). 

> [!IMPORTANT]
> The verification loop proves that Multi-Agent verification is highly effective for catching anomalies, but it also demonstrates that **if the underlying model is not smart enough for the complexity of the task**, wrapping it in an agentic loop won't magically solve everything. 
> For highly complex financial math, you must use a smarter foundational model like `claude-sonnet-4.5` (which passed all these tests blindly in our previous example) alongside CoT for guaranteed safety.

## 4. Tool-Augmented Verification
**Script:** [verification_loop_example.py](file:///d:/Source/Learning/ClaudeArchitectExamples/verification_loop_example.py)

**What we did:** We upgraded Agent B in our Verification Loop with a `calculate` tool using LangGraph. We prompted it: *"You MUST use the calculate tool for ALL mathematical operations."*
**The Result: PERFECT SUCCESS ✅**
When forced to explicitly invoke the calculator tool, Haiku could no longer jump to faulty conclusions (like hallucinating the remaining unit count). It wrote out exactly what parameters to send to the calculator (`50000000 - 2500000 - 1000000`), which returned `46500000`, perfectly fixing the error! 

This proves that forcing tool use creates an **"Accidental Scratchpad"** effect, combining the logic improvements of Chain of Thought with the flawless math execution of a Python calculator!
