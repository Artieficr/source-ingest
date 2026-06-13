---
title: "US Court Rulings on AI Training and Copyright (2023-2025)"
aliases:
  - "US Court Rulings on AI Training and Copyright (2023-2025)"
category: background
source: "[[LLM Data Usage Verification]]"
created: 2026-06-14
related: ["[[the-llm-training-data-verification-gap]]", "[[major-llm-providers-public-data-use-policies-for-training]]", "[[how-llm-training-pipelines-process-data]]", "[[eu-and-uk-regulatory-approaches-to-ai-training-data]]", "[[documented-incidents-and-evidence-related-to-undisclosed-ai-training-data-use]]", "[[empirical-methods-for-detecting-whether-specific-data-was-used-in-training]]", "[[proposed-technical-solutions-for-verifying-ai-training-data-use]]", "[[policy-and-practical-recommendations-for-ai-training-data-transparency]]"]
conflicts: []
---
# US Court Rulings on AI Training and Copyright (2023-2025)

## Content
US courts have issued several significant and partly conflicting rulings on whether training AI models on copyrighted material constitutes fair use, alongside a major US Copyright Office report.

On May 9, 2025, the U.S. Copyright Office released a 108-page report on AI training and fair use, urging caution. It concluded that using copyrighted works for training is not automatically fair use, that AI training can produce "perfect copies" of expressions internally even if not reproduced in outputs, and that courts should consider "market dilution" -- whether a model's outputs compete with the style or genre of the works it was trained on. The report rejected simplistic analogies between AI training and human learning and suggested that some large-scale, commercial, unlicensed training goes beyond established fair use boundaries, though it stopped short of recommending new legislation.

In Thomson Reuters v. Ross (D. Del., 2023), Judge Bibas ruled against Ross Intelligence, which had trained a legal AI on Thomson Reuters' Westlaw headnotes without permission and had attempted to hide this. The court found the training itself -- not just the output -- was infringing, because Ross was a direct competitor, the use was nontransformative, and it threatened Reuters' market for those headnotes, even though Ross's outputs did not directly regurgitate the text.

In Bartz v. Anthropic (N.D. Cal., June 2025), Judge Alsup ruled that training Claude on legally purchased books was "exceedingly transformative" and therefore fair use, comparing it to how humans learn from reading, partly because Anthropic's filters blocked verbatim reproduction and there was no evidence of market harm. However, he ruled that downloading millions of pirated ebooks to build a training library was not fair use, and warned that evidence of output copying could have changed his ruling.

In Kadrey v. Meta (N.D. Cal., June 2025), Judge Chhabria reached a similar fair-use conclusion for Meta's LLaMA training on books, emphasizing that the plaintiffs failed to show actual market harm since LLaMA could not reproduce substantial portions of their books. Chhabria explicitly cautioned that this ruling does not broadly bless AI training generally -- it only reflects that these particular plaintiffs made the wrong arguments. Other cases, including New York Times v. Microsoft, Buchwald v. Meta, and Getty v. Stability AI (covering images), remain pending, with courts expected to continue weighing transformative purpose and market effects case-by-case.
