# Notes

## 28 Oct 11 AM
We would like coding agents to write Rust that [Aeneas](https://github.com/AeneasVerif/aeneas) can translate.
    


1. A simple starting point is a skill that calls a deterministic script to check whether code translates through Charon and Aeneas to Lean. ** The user might give it a crate, one file, or a few selected lines. 
Start with one case and explain how you would handle the others: 
>Idea is to build a collection of tests that pass/fail translation to lean.
>Also have tests that document options which include/exclude code
what surrounding code and dependencies are needed, and 
>Make sure Aeneas fills up stdlib bodies

what did you actually check? 
>How to actually check that all code is translated?

Distinguish unsupported code from missing context or a toolchain problem.

2. The same skill, or a sibling skill, could patch code that fails translation. 
Preserve its behaviour and show the diff. 

Hiding unsupported code behind unchecked stubs does not count as a repair.
>Repair involves transforming unsupported code to supported programming paradigm E.g., unsafe code to safe code

Successful translation alone is not a correctness proof.
>Agreed

3. The harder question is how to get compatible Rust on the first attempt, without a generate/check/patch loop. 

A strategy is enough here; implementation would likely take more than eight hours. 

Fine-tuning and other techniques for local inference with open-source models are welcome. 

Also suggest a way to bring the benefits to existing personal or enterprise subscriptions, such as Claude Code, Codex or subscription-backed open models, without requiring custom weights or per-token API access. Check what your chosen plan allows.
>Use normal AI interface