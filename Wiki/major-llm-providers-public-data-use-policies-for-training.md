---
title: "Major LLM Providers' Public Data-Use Policies for Training"
aliases:
  - "Major LLM Providers' Public Data-Use Policies for Training"
category: typology
source: "[[LLM Data Usage Verification]]"
created: 2026-06-14
related: ["[[the-llm-training-data-verification-gap]]", "[[how-llm-training-pipelines-process-data]]", "[[us-court-rulings-on-ai-training-and-copyright-2023-2025]]", "[[eu-and-uk-regulatory-approaches-to-ai-training-data]]", "[[documented-incidents-and-evidence-related-to-undisclosed-ai-training-data-use]]", "[[empirical-methods-for-detecting-whether-specific-data-was-used-in-training]]", "[[proposed-technical-solutions-for-verifying-ai-training-data-use]]", "[[policy-and-practical-recommendations-for-ai-training-data-transparency]]"]
conflicts: []
---
# Major LLM Providers' Public Data-Use Policies for Training

## Content
Public data-use policies vary significantly across major LLM providers, though a common pattern is that paid/enterprise tiers disclaim training use by default while free/consumer tiers often permit it unless the user opts out.

OpenAI (ChatGPT, GPT APIs) by default collects and may use free and Plus users' conversations to improve and train models, though users can disable the "Improve the model for everyone" / share-data toggle to exclude new chats; previously submitted conversations remain stored unless separately deleted. Enterprise, Business, and API customers are "privacy-first" -- by default their inputs are not used for training, per OpenAI's Enterprise Privacy Policy ("we do not train our models on your data by default").

Anthropic (Claude) mirrors this structure: commercial products (Claude for Work, Claude API) are not used for training by default except for voluntary feedback, while consumer products (Free, Pro, Max) are only used for training if the user opts in. Incognito-mode chats are never used for training regardless of other settings. Starting Fall 2025, Anthropic announced it would require explicit opt-in for all consumer accounts and extend data retention for active accounts to five years.

Google (Gemini/Bard) is comparatively opaque. Turning off "Keep Activity" stops personalized suggestions, but Google's own privacy materials state that chats may still be used in anonymized, aggregated form to train models even with activity history off; human reviewers may see anonymized snippets, retained for up to three years (or up to 18 months per other analyses). There is no clear per-prompt opt-out for consumer Gemini, though a Workspace/Enterprise offering claims private content handling without public detail.

Microsoft's enterprise products (Copilot for Microsoft 365, Azure OpenAI) explicitly state that prompts, responses, and data accessed are not used to train foundation models, and Azure OpenAI customers can opt out of data logging. Consumer Bing Chat has no public commitment either way.

Meta (LLaMA, Meta AI) announced in early 2025 that it would train on EU users' interactions and public posts, with an EU-only opt-out form required by law; outside the EU its policy is less transparent, though it presumably uses public data similarly. Meta has no enterprise LLM service comparable to the others.

Amazon Bedrock takes the strictest stance: customer inputs and outputs are never used to train Amazon's base models, fine-tuned models are isolated as private copies, and this applies to all Bedrock customers by default with no opt-out needed.
