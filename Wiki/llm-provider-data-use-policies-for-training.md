---
title: "LLM Provider Data-Use Policies for Training"
aliases:
  - "LLM Provider Data-Use Policies for Training"
category: typology
source: "[[LLM Data Usage Verification]]"
created: 2026-06-15
related:
  - "[[architecture-of-llm-training-data-pipelines]]"
  - "[[the-llm-training-verification-gap]]"
  - "[[us-copyright-office-2025-report-on-ai-training-and-fair-use]]"
  - "[[key-us-court-rulings-on-ai-training-data]]"
  - "[[eu-and-uk-regulatory-approaches-to-ai-training-data]]"
  - "[[documented-incidents-and-whistleblower-reports-on-ai-training-data]]"
  - "[[empirical-methods-for-detecting-whether-data-was-used-in-llm-training]]"
  - "[[proposed-technical-solutions-for-verifying-ai-training-data-use]]"
  - "[[policy-and-regulatory-options-for-ai-training-transparency]]"
  - "[[practical-recommendations-for-creators-users-and-policymakers-on-ai-training-data]]"
conflicts: []
---
# LLM Provider Data-Use Policies for Training

## Content
Major LLM providers offer differing public commitments about whether user inputs are used to train their models, and the policies vary sharply between free/consumer tiers and paid/enterprise tiers.

OpenAI (ChatGPT, GPT APIs): free and Plus users have their conversations used by default to improve and train models, unless they disable the "Improve the model for everyone" / "Share Data" toggle, which stops future chats from entering the training pipeline (past chats already stored remain unless deleted). Enterprise, Business, and API customers are "privacy-first" — by default their inputs are not used for training, per OpenAI's Enterprise Privacy Policy ("we do not train our models on your data by default"). No independent audits exist; OpenAI has faced multiple copyright lawsuits and an FTC inquiry.

Anthropic (Claude): for commercial products (Claude for Work, Claude API), inputs/outputs are not used for training by default, except via voluntary feedback. For consumer products (Claude Free/Pro/Max), training on chats only happens if the user opts in; "Incognito" (Safe Completion) chats are never used for training even if data sharing is enabled. Anthropic announced that starting Fall 2025 it would require explicit opt-in for all consumer accounts, alongside extending data retention for active accounts to five years. Deleting an account or changing settings excludes data from future training.

Google (Gemini/Bard): policies are vague and opaque. Turning off "Keep Activity" stops personalization, but Google's own privacy hub states chats may still be used in anonymized form to train AI models even with activity off. Human reviewers may see anonymized chat snippets, retained for up to 3 years (some analyses cite up to 18 months for data retention). There is no clear per-prompt opt-out. A Workspace/enterprise Gemini offering claims content isn't used for training, but detailed terms aren't public.

Microsoft (Copilot, Bing, Azure OpenAI): enterprise products (Microsoft 365 Copilot, Azure OpenAI) explicitly do not use customer prompts, responses, or Graph-accessed data to train foundation LLMs, and Azure OpenAI customers can opt out of data logging. Consumer Bing Chat has no public commitment either way and likely logs data internally.

Meta (LLaMA, Meta AI): no formal free/paid tier distinction. In early 2025 Meta announced it would train its AI on EU users' interactions and public posts, with EU users able to opt out via an online form; private messages are excluded unless shared. Outside the EU, Meta has disclosed little but presumably uses public data. No enterprise LLM product exists comparable to Bedrock or Azure OpenAI.

Amazon (Bedrock): the strictest stance — customer inputs and outputs are never used to train Amazon's base models, and fine-tuned models are isolated per customer in encrypted, separate storage. This applies to all Bedrock customers by default, backed by enterprise contracts and compliance certifications.

Overall pattern: paid/enterprise tiers generally default to "no training" (OpenAI, Anthropic, Microsoft, Amazon); free/consumer tiers default to training unless the user opts out (OpenAI, Anthropic); Google leans on "aggregate use" regardless of toggles; Meta's policy is region-dependent and new. No company offers verifiable proof of what data actually entered training.
