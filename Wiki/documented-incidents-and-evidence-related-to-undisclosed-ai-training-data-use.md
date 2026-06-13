---
title: "Documented Incidents and Evidence Related to Undisclosed AI Training Data Use"
aliases:
  - "Documented Incidents and Evidence Related to Undisclosed AI Training Data Use"
category: background
source: "[[LLM Data Usage Verification]]"
created: 2026-06-14
related: ["[[the-llm-training-data-verification-gap]]", "[[major-llm-providers-public-data-use-policies-for-training]]", "[[how-llm-training-pipelines-process-data]]", "[[us-court-rulings-on-ai-training-and-copyright-2023-2025]]", "[[eu-and-uk-regulatory-approaches-to-ai-training-data]]", "[[empirical-methods-for-detecting-whether-specific-data-was-used-in-training]]", "[[proposed-technical-solutions-for-verifying-ai-training-data-use]]", "[[policy-and-practical-recommendations-for-ai-training-data-transparency]]"]
conflicts: []
---
# Documented Incidents and Evidence Related to Undisclosed AI Training Data Use

## Content
As of the report, no whistleblower has exposed an LLM provider secretly violating its own stated data-use policy, but several related incidents and findings illustrate the risks involved.

Court filings (rather than whistleblowers) revealed in 2024 that several AI companies, including Anthropic, had purchased and scanned millions of physical books -- sometimes from questionable sources -- to use as training data. Separately, researchers have demonstrated that models can "leak" memorized training content under certain conditions: early work showed GPT-2 could be induced to output memorized excerpts, and later research (e.g., "Training Data Is All You Need," ICLR 2023) showed training text could sometimes be regenerated through careful probing. This does not prove any specific leak occurred, but it shows that if a model was trained on particular copyrighted text, that text could in principle resurface in outputs -- a risk cited by plaintiffs in lawsuits.

When Anthropic introduced a "Safe Completion" or incognito-style mode for Claude, where user messages would not be used for training, it raised questions about what happens to flagged or sensitive chats -- Anthropic indicated such chats might still be used to refine safety systems, illustrating ambiguity about whether "incognito" data is truly excluded from all internal uses.

A small number of AI researchers and former employees, including Timnit Gebru, have raised general concerns about broad data collection practices by large tech companies, but these concerns have centered on AI safety rather than specific revelations about training data pipelines. Separately, independent researchers (including those at Mozilla) have audited public corpora like Common Crawl and found that, regardless of what companies claim about filtering, these widely used datasets do contain copyrighted and private material -- meaning that if providers rely on such corpora, copyrighted text may enter training sets even without any deliberate policy violation. Overall, the suspicion of improper data use comes primarily from inferred model behavior and litigation, not from any confirmed internal leak.
