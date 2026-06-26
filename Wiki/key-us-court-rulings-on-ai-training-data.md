---
title: "Key US Court Rulings on AI Training Data"
aliases:
  - "Key US Court Rulings on AI Training Data"
category: background
source: "[[LLM Data Usage Verification]]"
created: 2026-06-15
related:
  - "[[llm-provider-data-use-policies-for-training]]"
  - "[[architecture-of-llm-training-data-pipelines]]"
  - "[[the-llm-training-verification-gap]]"
  - "[[us-copyright-office-2025-report-on-ai-training-and-fair-use]]"
  - "[[eu-and-uk-regulatory-approaches-to-ai-training-data]]"
  - "[[documented-incidents-and-whistleblower-reports-on-ai-training-data]]"
  - "[[empirical-methods-for-detecting-whether-data-was-used-in-llm-training]]"
  - "[[proposed-technical-solutions-for-verifying-ai-training-data-use]]"
  - "[[policy-and-regulatory-options-for-ai-training-transparency]]"
  - "[[practical-recommendations-for-creators-users-and-policymakers-on-ai-training-data]]"
conflicts: []
---
# Key US Court Rulings on AI Training Data

## Content
Three major U.S. court decisions have shaped the legal picture for AI training on copyrighted material, with mixed outcomes.

Thomson Reuters v. Ross Intelligence (D. Del., 2023) was the first major AI-related copyright verdict outside California and sided with the copyright owner. Ross Intelligence had trained a legal AI on Thomson Reuters' Westlaw headnotes, attempting to conceal this. Judge Bibas ruled that copying the headnotes to build the AI was not fair use, citing that Ross was a direct competitor, the use was nontransformative, and it could harm Reuters' market for those headnotes — even though Ross's outputs didn't simply regurgitate the text. The case established that a commercial competitor training on proprietary content without permission carries significant legal risk, with the training step itself (not just the output) found infringing.

Bartz v. Anthropic (N.D. Cal., June 2025), decided by Judge Alsup (known for Oracle v. Google), reached the opposite conclusion for legally purchased material: training Claude on legally purchased books was held "exceedingly transformative" and therefore fair use, by analogy to how humans learn from reading, since Claude did not copy outputs verbatim. However, the same ruling found that downloading millions of pirated ebooks to build a training library was not fair use. The ruling was narrow — specific to Anthropic's practices, including its filters against exact reproduction — and Alsup indicated he might have ruled differently had there been evidence of output copying.

Kadrey v. Meta (N.D. Cal., June 2025), decided shortly after by Judge Chhabria, reached a similar fair-use outcome for Meta's LLaMA training on books, emphasizing lack of market impact: the plaintiffs couldn't show LLaMA could output substantial portions of their books, so their claim failed. Chhabria explicitly cautioned that this ruling doesn't broadly bless AI training — it only reflects that these particular plaintiffs made the wrong arguments and failed to build the right evidentiary record.

Other cases remain pending, including New York Times v. Microsoft, Buchwald v. Meta, and Getty Images v. Stability AI (image-based). The overall trend is that courts are weighing transformative purpose and market effects on a case-by-case basis, rather than establishing a single bright-line rule.
