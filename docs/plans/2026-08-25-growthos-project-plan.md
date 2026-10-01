# GrowthOS — Full Project Plan

**Date:** 2026-08-25  
**Status:** Product / architecture plan  
**Repository:** `swd07/growthos`
**Current state of the social layer:** [status and next tasks](2026-10-01-growthos-social-status.md)

## 1. Product vision

**GrowthOS** is an AI-native platform for growing any brand through organic content, video generation, paid advertising, cross-platform publishing, analytics, experimentation, and continuous learning.

The product should cover the full loop:

```text
Brand
  ↓
Brand Memory
  ↓
Research / Trends / Competitors
  ↓
Content Strategy
  ↓
Campaign Plan
  ↓
Content Factory
  ↓
Platform-specific adaptation
  ↓
Human approval / Autopilot
  ↓
Publishing
  ↓
Reddit / X / Instagram / TikTok / Facebook / YouTube
  ↓
Organic analytics + Ad analytics
  ↓
Experiments
  ↓
AI Growth Optimizer
  ↓
Next campaign
```

The key product idea is not “generate posts”. The platform should **learn what actually grows a specific brand and continuously improve the strategy**.

---

## 2. Product positioning

GrowthOS should be positioned as an **Autonomous Brand Growth Platform / AI Growth OS**, not a social scheduler.

The value proposition:

> Research → create → produce → publish → promote → measure → learn → repeat.

The same engine should work for:

- personal brands;
- AI / software companies;
- restaurants;
- real estate;
- fitness coaches;
- SaaS;
- e-commerce;
- agencies;
- local businesses;
- enterprise brands.

---

## 3. Claude Code, GPT, Qwen: clients/providers, not the platform core

Do **not** build the product as Claude Code directly calling social APIs.

Target architecture:

```text
                    ┌─ Web UI
                    │
Claude Code → MCP → GrowthOS API
                    │
                    ├─ Agents
                    ├─ Workflow Engine
                    ├─ Social Connectors
                    ├─ Content Factory
                    ├─ Video Factory
                    ├─ Ads Engine
                    └─ Analytics
```

GrowthOS must remain model-agnostic and expose its functionality to:

- Web UI;
- Claude Code via MCP;
- future internal agents;
- external API clients;
- automation workflows.

Supported model providers should be abstracted behind a common LLM gateway:

- Anthropic;
- OpenAI;
- Gemini;
- Qwen via self-hosted vLLM;
- future OpenAI-compatible providers.

---

## 4. MCP interface

GrowthOS should provide an MCP server so Claude Code or another MCP-capable agent can control the platform safely.

Proposed tools:

```text
brand.get
brand.get_memory
brand.update_memory

research.trends
research.competitors
research.audience

campaign.create
campaign.plan
campaign.get

content.ideate
content.generate
content.repurpose
content.review

image.generate

video.create_script
video.create_storyboard
video.generate_shots
video.render
video.create_thumbnail

social.preview
social.schedule
social.publish
social.get_status

analytics.get_posts
analytics.get_growth
analytics.compare
analytics.explain

experiment.create
experiment.evaluate

ads.create_draft
ads.preview
ads.launch
ads.pause
ads.optimize

report.weekly
```

Critical rule:

```text
generate ≠ publish
```

Publishing and advertising must require explicit permissions and approval policies.

---

## 5. Brand Workspace

Each customer creates one or more isolated **Brand Workspaces**.

A workspace should contain:

```text
brand_name
website
description
products
services
target_audience
countries
languages
tone_of_voice
brand_values
forbidden_topics
preferred_topics
competitors
offers
CTA
social_accounts
visual_style
logos
fonts
brand_assets
people/founders
past_content
successful_content
failed_content
```

### Brand Memory

Brand Memory is the persistent AI context used across every campaign.

Storage:

```text
PostgreSQL
+
pgvector
```

The memory layer should include:

- structured brand settings;
- source documents;
- website snapshots;
- product/service descriptions;
- previous campaigns;
- content performance;
- audience reactions;
- approved/rejected content;
- embeddings for semantic retrieval.

---

## 6. AI agent architecture

Avoid one giant “marketing agent”. Use specialized agents with clear responsibilities.

### 6.1 Brand Strategist

Responsible for:

- positioning;
- audience segmentation;
- value proposition;
- tone of voice;
- content pillars;
- competitive differentiation;
- messaging rules.

### 6.2 Research Agent

Researches:

- fresh trends;
- news;
- competitor activity;
- Reddit discussions;
- X discussions;
- audience pain points;
- search demand;
- emerging content angles.

### 6.3 Content Strategist

Decides:

```text
what to publish
where
why
for which audience
with which CTA
in which format
```

### 6.4 Copywriter Agent

Generates platform-native copy:

- posts;
- threads;
- captions;
- hooks;
- titles;
- descriptions;
- scripts;
- replies;
- ad copy.

### 6.5 Platform Adapter Agent

Converts one idea into native formats for each platform.

Example source idea:

> Why 429 is better than unlimited LLM queueing.

Variants:

- Reddit → detailed engineering discussion;
- X → thread;
- TikTok → 30–60 second video;
- Instagram → Reel + caption;
- YouTube → long-form video;
- YouTube Shorts → vertical short;
- Facebook → post/video variation.

Data model:

```text
ContentIdea
    ↓
PlatformVariant[]
```

---

## 7. Content Factory

Core media types:

```text
TEXT
IMAGE
AUDIO
VIDEO
```

Text generation should support:

- posts;
- long-form articles;
- threads;
- scripts;
- titles;
- captions;
- descriptions;
- hashtags;
- hooks;
- CTAs;
- comments;
- replies;
- ad variants.

Every generated asset should preserve provenance:

```text
brand
campaign
source idea
model/provider
prompt version
agent run
review status
```

---

## 8. Video Factory

Video is a major differentiator and should be designed as a full production pipeline rather than a single generation call.

Pipeline:

```text
idea
 ↓
script
 ↓
hook variants
 ↓
storyboard
 ↓
shot list
 ↓
asset selection
 ↓
AI video generation
 ↓
voice generation
 ↓
screen recordings / screenshots
 ↓
captions
 ↓
music
 ↓
branding
 ↓
render
 ↓
9:16 / 16:9 / 1:1
```

### Provider abstraction

```python
class VideoProvider:
    generate(prompt)
    extend(video)
    image_to_video(...)
    status(...)
```

Adapters may include:

```text
SeedanceProvider
VeoProvider
KlingProvider
RunwayProvider
...
```

Routing should be based on content type and economics:

```text
cinematic → provider A
human presenter → provider B
fast/cheap shorts → provider C
```

---

## 9. Video rendering / assembly engine

Generated clips alone are not enough.

Recommended stack:

```text
Remotion
+
FFmpeg
```

The rendering engine assembles:

- generated video clips;
- voiceover;
- subtitles;
- background music;
- logos;
- lower thirds;
- animations;
- screenshots;
- code snippets;
- charts;
- call-to-action cards.

Output presets:

- 9:16 TikTok / Reels / Shorts;
- 16:9 YouTube;
- 1:1 social feed;
- platform-specific safe zones and bitrate presets.

---

## 10. Social integration layer

Common interface:

```python
class SocialProvider:
    authenticate()
    publish()
    schedule()
    delete()
    get_post()
    get_metrics()
```

Providers:

```text
XProvider
MetaProvider
TikTokProvider
YouTubeProvider
RedditProvider
```

Each provider must handle:

- OAuth/token lifecycle;
- scopes;
- upload limits;
- media processing;
- rate limits;
- retries;
- idempotency;
- publishing status;
- platform-specific metadata;
- metrics ingestion.

---

## 11. Platform rollout strategy

### 11.1 X

Support:

- text posts;
- threads;
- images;
- videos;
- scheduled publishing;
- metrics retrieval.

### 11.2 TikTok

Support:

- Direct Post where app permissions/audit allow it;
- draft upload fallback;
- video/photo publishing;
- AI-generated content metadata;
- publishing status polling.

### 11.3 YouTube

Support:

- video upload;
- Shorts;
- title/description/tags;
- thumbnails;
- playlist placement;
- processing status;
- analytics.

### 11.4 Instagram + Facebook

Treat Meta as one ecosystem with two product surfaces.

Organic:

```text
Meta Graph APIs
```

Paid:

```text
Meta Marketing API
```

Support:

- Instagram feed;
- Reels;
- Facebook Page posts;
- images;
- video;
- publishing status;
- analytics;
- later: paid campaigns.

### 11.5 Reddit

Reddit should be isolated behind its own adapter because its developer platform and automation rules are changing.

Initial product mode:

```text
AI creates Reddit post
       ↓
User approves
       ↓
Open Reddit / copy prepared content
       ↓
Manual publish
       ↓
GrowthOS tracks the final URL
```

Full automated publishing should only be enabled through an officially supported and compliant integration path.

---

## 12. Publishing Engine

Use a durable workflow engine rather than cron jobs plus ad-hoc queues.

Recommended:

```text
Temporal
```

Example workflow:

```text
PublishWorkflow

wait_until(schedule_time)
validate_token()
validate_content()
publish()

if processing:
    poll_status()

if rate_limit:
    retry()

fetch_public_url()
save_result()
schedule_metrics_collection()
```

Requirements:

- durable schedules;
- idempotency;
- retries;
- backoff;
- workflow state;
- visibility;
- manual intervention;
- dead-letter handling.

---

## 13. Approval system

Lifecycle:

```text
IDEA
↓
DRAFT
↓
GENERATING
↓
READY_FOR_REVIEW
↓
APPROVED
↓
SCHEDULED
↓
PUBLISHING
↓
PUBLISHED
```

Additional states:

```text
REJECTED
FAILED
PAUSED
```

Audit fields:

```text
created_by_agent
approved_by_user
published_by_system
created_at
approved_at
published_at
```

---

## 14. Automation modes

### Manual

AI prepares content only.

### Assisted

AI researches, prepares, and schedules; user approves.

### Autopilot

AI performs the loop automatically within policy limits:

```text
research
→ generate
→ schedule
→ publish
→ analyze
→ optimize
```

Guardrails:

```text
max_posts_per_day
allowed_platforms
forbidden_topics
allowed_ad_budget
languages
approval_rules
brand-risk rules
```

Autopilot is **not an MVP feature** and should only be enabled after sufficient reliability data exists.

---

## 15. Analytics model

Normalize common metrics across platforms:

```text
impressions
reach
views
likes
comments
shares
saves
clicks
followers
watch_time
avg_watch_time
retention
CTR
conversion
revenue
```

Also keep raw platform-specific metrics.

Every content item should store explanatory features:

```text
topic
hook
format
duration
platform
posting_time
CTA
tone
video_style
speaker
model
hashtags
```

This makes it possible to correlate content choices with outcomes.

---

## 16. Content Intelligence

The platform should learn brand-specific patterns such as:

> Technical failure stories outperform generic AI news on Reddit.

> 28–42 second videos create more profile visits than 60+ second videos.

> Architecture diagrams create more GitHub clicks on X.

The system should convert analytics into concrete strategy changes rather than generic reports.

---

## 17. Experiment Engine

Support controlled content experiments.

Examples:

```text
Hook A / B / C
30 sec / 60 sec / 90 sec
technical / storytelling / provocative
thumbnail A / B
CTA A / B
```

Initial implementation:

- explicit experiment configuration;
- comparable audience/time windows where possible;
- confidence and sample-size warnings;
- human-readable conclusions.

Future implementation:

- contextual bandits;
- automatic allocation;
- adaptive experimentation.

Not required for MVP.

---

## 18. AI Growth Optimizer

Higher-level learning loop:

```text
collect metrics
      ↓
normalize
      ↓
compare campaigns
      ↓
detect patterns
      ↓
generate hypotheses
      ↓
recommend experiments
      ↓
update strategy
```

Example output:

> Stop generic news on Reddit.

> Increase production-AI case studies from 2 to 4 per week.

> Convert the best X thread into a YouTube Short.

> Qwen content generated 2.6× more profile visits than generic GPT content.

---

## 19. Ads Engine

Paid advertising must be a separate bounded subsystem.

Architecture:

```text
Ad Strategy
 ↓
Creative Generation
 ↓
Ad Draft
 ↓
Budget Simulation
 ↓
Human Approval
 ↓
Campaign Launch
 ↓
Performance Monitoring
 ↓
Optimization Recommendation
```

Future connectors:

```text
Meta Ads
Google / YouTube Ads
TikTok Ads
X Ads
Reddit Ads
```

AI must never receive unrestricted spending authority.

Guardrails:

- per-campaign budget;
- daily budget;
- account budget;
- geographic limits;
- objective restrictions;
- approval threshold;
- pause rules;
- anomaly detection.

---

## 20. Organic → Paid promotion

A key differentiator should be automatic identification of high-performing organic content.

Example:

```text
3× average watch time
2× saves
4× shares
```

GrowthOS can recommend:

> This content is in the top 5% of your last 90 days. Test it as a paid creative.

Then generate:

```text
creative A/B/C
headline A/B
CTA A/B
audience suggestions
budget suggestion
```

The actual campaign should still require explicit approval in initial versions.

---

## 21. Conversion tracking and attribution

Required components:

```text
UTM generator
short links
tracking IDs
pixels
server-side events
conversion API adapters
```

Target chain:

```text
Reddit / X / TikTok / YouTube
 ↓
Website
 ↓
Signup
 ↓
Lead
 ↓
Paid customer
```

The system must eventually understand:

```text
Revenue attributable to campaign X
```

---

## 22. Backend stack

Recommended:

```text
Python 3.13
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
pgvector
Redis
Temporal
S3-compatible storage
```

LLM layer:

```text
OpenAI-compatible abstraction
```

Providers:

```text
Anthropic
OpenAI
Gemini
Qwen/vLLM
other providers
```

---

## 23. Frontend stack

Recommended:

```text
Next.js
TypeScript
React
Tailwind
shadcn/ui
```

Primary screens:

| Screen | Purpose |
|---|---|
| Dashboard | Brand status and growth overview |
| Brand Memory | Brand knowledge and constraints |
| Campaigns | Campaign planning and execution |
| Calendar | Content calendar |
| Studio | Text/image content generation |
| Video Studio | Script/storyboard/render workflow |
| Approvals | Human review queue |
| Social Accounts | Connected accounts and permissions |
| Analytics | Performance metrics |
| Experiments | A/B tests |
| Ads | Paid campaigns |
| Agent Runs | AI actions and reasoning summaries |
| Settings | Workspace configuration |

---

## 24. Codebase architecture

Start with a **modular monolith**, not microservices.

```text
growthos/
│
├── apps/
│   ├── web/
│   └── api/
│
├── modules/
│   ├── brands/
│   ├── campaigns/
│   ├── content/
│   ├── analytics/
│   ├── ads/
│   ├── approvals/
│   └── billing/
│
├── agents/
│
├── providers/
│   ├── social/
│   ├── llm/
│   ├── image/
│   ├── video/
│   └── tts/
│
├── workflows/
│
├── media-worker/
│
├── mcp-server/
│
└── infra/
```

Extract services only when scale/operational needs justify it.

Likely future service boundaries:

```text
video rendering
analytics ingestion
generation workers
high-volume publishing
```

---

## 25. Core database entities

```text
users
organizations
brands

brand_documents
brand_assets
brand_memory

social_accounts
social_tokens

campaigns
campaign_goals

content_ideas
content_variants
content_assets

videos
video_shots

approvals

publish_jobs
published_posts

metrics_snapshots

experiments
experiment_variants

ad_accounts
ad_campaigns
ad_creatives
ad_metrics

agent_runs
model_calls
costs

audit_logs
```

---

## 26. Multi-tenancy

Design multi-tenant from day one.

```text
Organization
   ├── Brand A
   ├── Brand B
   └── Brand C
```

This allows future support for:

- creators;
- SMBs;
- agencies;
- enterprise teams.

Agency scenario:

```text
1 agency
30+ client brands
many social accounts
multiple team members
```

---

## 27. Security

Must not be deferred.

OAuth and social tokens:

```text
encrypted at rest
```

Secrets:

```text
Vault / KMS
```

RBAC:

```text
Owner
Admin
Editor
Reviewer
Viewer
```

Other requirements:

```text
tenant isolation
audit logs
token rotation
least-privilege scopes
rate limiting
access logging
data deletion workflows
```

---

## 28. Brand safety and AI pre-publish gates

Every publishable asset should pass a safety/quality gate.

Checks:

```text
hallucinations
URLs
names
numbers
claims
competitors
prohibited topics
legal statements
medical/financial claims
brand rules
platform policy flags
```

Advertising should have stricter validation than organic content.

---

## 29. Observability

### Infrastructure

```text
latency
errors
queues
CPU
GPU
jobs
API availability
```

### Social integrations

```text
token expiration
rate limits
publish failures
processing failures
API changes
```

### AI

```text
provider
model
tokens
latency
generation cost
accepted/rejected
```

Recommended stack:

```text
OpenTelemetry
Prometheus
Grafana
Sentry
```

---

## 30. Cost accounting

Every AI/media action must have cost attribution.

Example:

```text
Claude tokens       $0.08
video generation    $0.76
TTS                 $0.02
image               $0.04
render               $0.01
```

Costs must be linked to:

```text
brand
campaign
content
user
provider
model
```

This is mandatory for SaaS unit economics and future billing.

---

## 31. MVP 0 — dogfooding

Start with one real brand and use GrowthOS internally before selling it.

Initial functional scope:

```text
Brand Memory
Content ideas
Claude/Qwen generation
X
YouTube
TikTok
Meta
Calendar
Approval
Publishing
Metrics
MCP
```

Reddit begins as assisted/manual publish.

Video MVP:

```text
script
voice
captions
basic AI video/assets
render
```

---

## 32. MVP acceptance criteria

A release is considered a functional MVP when the following request works end-to-end:

> Create a campaign about Qwen for next week.

System behavior:

1. reads Brand Memory;
2. proposes 5 relevant topics;
3. creates a weekly content plan;
4. generates Reddit/X variants;
5. generates 3 Shorts/Reels/TikTok variants;
6. creates a YouTube script;
7. shows previews;
8. receives approval;
9. publishes/schedules through supported APIs;
10. collects metrics;
11. generates a weekly analysis;
12. recommends the next campaign.

If this complete vertical slice works reliably, GrowthOS is already a usable product.

---

## 33. Roadmap

| Phase | Estimated time | Result |
|---|---:|---|
| Phase 0 | 1 week | Architecture, schemas, API contracts |
| Phase 1 | 2 weeks | Auth, organizations, brands, Brand Memory |
| Phase 2 | 2 weeks | AI agents, campaigns, content factory |
| Phase 3 | 2 weeks | X + Meta connectors |
| Phase 4 | 2 weeks | YouTube + TikTok connectors |
| Phase 5 | 2 weeks | Temporal scheduler + approvals |
| Phase 6 | 2 weeks | Analytics ingestion and dashboard |
| Phase 7 | 2 weeks | Video factory |
| Phase 8 | 1 week | MCP server for Claude Code |
| Phase 9 | 2 weeks | Ads MVP |
| Phase 10 | 2 weeks | Hardening + private beta |

Target:

- aggressive dogfood version: **6–8 weeks**;
- serious private beta: **~4–5 months**.

The largest schedule uncertainty is external app review and social-platform permissions, not core engineering.

---

## 34. Explicitly out of scope for the first version

Do not build initially:

- own foundation video model;
- own LLM;
- complex recommender ML;
- dozens of social platforms;
- fully autonomous comments/replies;
- CRM;
- full DAM suite;
- enterprise SSO;
- sophisticated multi-touch attribution;
- real-time bidding;
- large multi-agent swarm.

These can consume months without proving the core loop.

---

## 35. V2 — Paid Growth

After organic MVP:

```text
Meta Ads
Google / YouTube Ads
TikTok Ads
X Ads
```

Capabilities:

```text
campaign creation
creative generation
A/B tests
budgets
conversion tracking
ROAS
recommendations
```

---

## 36. V3 — Autonomous Growth

Target long-term loop:

```text
Research
 ↓
Hypothesis
 ↓
Campaign
 ↓
Generate
 ↓
Publish
 ↓
Measure
 ↓
Experiment
 ↓
Learn
 ↓
Reallocate effort/budget
```

Autopilot may eventually change:

- publication frequency;
- platform mix;
- content format mix;
- testing priorities;
- paid budget allocation;

but only inside explicit user-defined risk and budget constraints.

---

## 37. V4 — Agency Platform

Target scale:

```text
50 brands
300 social accounts
20 users
```

Agency features:

- white label;
- client approval portal;
- reusable brand templates;
- account manager roles;
- consolidated analytics;
- bulk operations;
- customer-specific permissions.

---

## 38. Monetization

Recommended structure:

```text
Subscription
+
AI usage
+
Video credits
```

Potential tiers:

### Creator

- 1 brand;
- basic social publishing;
- limited AI usage.

### Pro

- several brands;
- video generation;
- advanced analytics;
- experiments.

### Agency

- many brands;
- team/RBAC;
- client approvals;
- consolidated analytics.

### Enterprise

- SSO;
- private models;
- on-prem/VPC;
- SLA;
- custom connectors.

Avoid unlimited expensive video generation in a low fixed-price plan.

---

## 39. Competitive moat

Individual features are commodities:

- scheduler;
- copy generator;
- AI video generator;
- analytics dashboard.

The differentiator is the integrated loop:

```text
Brand intelligence
+
Content generation
+
Video generation
+
Cross-platform publishing
+
Ads
+
Analytics
+
Experimentation
+
Learning loop
+
Agent/MCP interface
```

Sell the outcome:

> GrowthOS discovers what content grows your brand, produces it, distributes it, measures the result, and continuously improves the strategy.

---

## 40. Dogfooding strategy

The first brand should use GrowthOS to grow itself / its founder.

All activity should gradually move through the platform:

```text
Reddit discussions
X posts
GitHub traffic
YouTube
TikTok
Instagram
Facebook
```

This produces:

```text
real users
real API failures
real platform limits
real performance data
real A/B tests
real case studies
```

Future case study:

> We built an AI growth platform and used it to grow its founder's technical brand from zero.

This lets product development and marketing reinforce each other.

---

## 41. First engineering milestone

Do **not** begin with full video or advertising.

Build one vertical slice first:

```text
Brand Workspace
      ↓
Brand Memory
      ↓
Campaign Agent
      ↓
Generate one idea
      ↓
X + Reddit + YouTube + TikTok variants
      ↓
Approval
      ↓
Publishing adapters
      ↓
Metrics
      ↓
Weekly AI report
      ↓
Claude Code MCP
```

If this works reliably, subsequent modules can be added incrementally.

---

## 42. Architecture decisions to lock now

1. **GrowthOS is a standalone SaaS platform.**
2. **Claude Code, GPT and Qwen are clients/providers, not the product foundation.**
3. **Publishing and ad-spend actions are separated from generation.**
4. **Human approval is default; Autopilot comes later.**
5. **Platform integrations are adapter-based.**
6. **Video providers are replaceable.**
7. **Start as a modular monolith.**
8. **Use durable workflows for scheduled/publishing operations.**
9. **Design multi-tenant from day one.**
10. **Analytics and cost attribution are first-class product features.**
11. **Dogfood on a real brand before external launch.**
12. **External API/app-review constraints are part of the product architecture, not an afterthought.**

---

## 43. Immediate next steps

### Step 1 — repository cleanup / project definition

- decide whether the current `ai-marketing-platform` repository becomes GrowthOS or a new code root is created inside it;
- add product README;
- add architecture decision records (ADRs);
- define terminology: Brand, Campaign, ContentIdea, PlatformVariant, PublishJob, Experiment.

### Step 2 — architecture package

Create:

```text
docs/specs/domain-model.md
docs/specs/api-contracts.md
docs/specs/social-provider-interface.md
docs/specs/mcp-interface.md
docs/specs/security-model.md
docs/specs/analytics-model.md
```

### Step 3 — MVP implementation order

1. auth / organizations / tenants;
2. brand workspace;
3. Brand Memory;
4. campaign + content domain model;
5. AI provider abstraction;
6. content generation;
7. approval workflow;
8. first social connector;
9. metrics ingestion;
10. weekly report;
11. MCP server;
12. video pipeline;
13. remaining platform connectors;
14. paid advertising.

### Step 4 — first real campaign

Use the platform to run one complete real campaign and record:

- time saved;
- number of generated assets;
- approval rate;
- publish success rate;
- platform failures;
- views/reach;
- profile visits;
- followers;
- link clicks;
- conversions;
- AI/media cost.

That campaign becomes both the MVP acceptance test and the first public case study.
