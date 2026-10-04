# GrowthOS — AI Marketing Operator (Draft Product Plan)

**Date:** 2026-10-04  
**Status:** Draft / product direction, not an implementation commitment  
**Repository:** `swd07/growthos`  
**Related:** [existing project plan](2026-08-25-growthos-project-plan.md) · [current social status](2026-10-01-growthos-social-status.md) · [social provider interface](../specs/social-provider-interface.md)

---

## 1. Product thesis

GrowthOS should not be positioned as a generic "AI platform for any business process" in its first market version.

The initial product should be focused and understandable:

> **GrowthOS is an AI marketing operator for founders, experts, consultants, and small teams.**

It should not stop at generating content. The product should run a complete marketing loop:

```
understand brand
    ↓
research
    ↓
strategy
    ↓
plan
    ↓
create
    ↓
approve
    ↓
publish
    ↓
engage
    ↓
measure
    ↓
learn
    ↓
adapt the next cycle
```

Externally, GrowthOS is a vertical marketing product.

Internally, it should be built on a reusable business-agent harness so that other vertical packs can be added later.

```
GrowthOS Core
    ├── Marketing Pack   ← first product
    ├── Sales Pack       ← later
    ├── Support Pack     ← later
    ├── Recruiting Pack  ← later
    └── Operations Pack  ← later
```

The architecture may be general. The go-to-market message should not be.

---

## 2. First customer: dogfood the product

The first real user should be Eduard himself.

The initial use case is:

> Build and grow Eduard's international personal brand as an AI Engineer / Applied AI specialist.

Primary channels:

- Instagram first
- LinkedIn second
- Telegram where useful
- personal website / landing page
- additional channels later

This gives GrowthOS a real production environment instead of a fake demo brand.

The system should eventually make it possible to say:

> "This account is operated with GrowthOS. Here is where it started, what the system did, what content it created, what it learned, and what business results followed."

The first proof should not be "we generated 100 posts." It should be measurable outcomes such as:

- reach
- profile visits
- followers
- saves and shares
- meaningful conversations
- inbound opportunities
- qualified leads
- time saved
- cost per content cycle

---

## 3. Initial ICP

The first ICP is deliberately narrow:

- founders
- technical founders
- experts / consultants
- solo operators
- small professional teams
- people building a personal brand around expertise

Common problem:

They know their subject, but do not want to spend every day doing this manually:

```
find topic
→ research
→ plan
→ write
→ make visual/video
→ publish
→ reply
→ inspect analytics
→ decide what to do next
```

GrowthOS should take over most of that operational loop while keeping the human in control.

---

## 4. Core product loop

The central product loop is:

```
Brand Context
    ↓
Research
    ↓
Strategy
    ↓
Content Plan
    ↓
Create
    ↓
Approve
    ↓
Publish
    ↓
Engage
    ↓
Measure
    ↓
Learn
    ↓
Next Strategy
```

This loop is more important than any individual content-generation feature.

A post, a Reel, or a chat response is only one step inside the system.

---

## 5. Brand Context / Brand Memory

GrowthOS needs a persistent representation of the person or company it operates for.

For Eduard, this would include information such as:

```
Identity
- Eduard
- AI Engineer / Applied AI

Topics
- AI agents
- LLM
- RAG
- multimodal AI
- AI infrastructure
- production AI
- computer vision
- self-hosted LLM
- agent harnesses

Audience
- founders
- CTOs
- AI engineers
- technical recruiters
- potential consulting clients

Goals
- build reputation
- grow relevant audience
- find international work
- attract consulting opportunities
- generate qualified leads

Tone
- technical
- human
- practical
- no guru-style hype

Constraints
- no invented achievements
- no unverified metrics
- no confidential employer information
- no claims outside verified experience
```

Brand assets may include:

- photos
- logo
- fonts
- color palette
- visual references
- projects
- GitHub
- articles
- website
- CV
- case studies
- previous publications

This becomes the stable **Brand Memory** used by other workflows.

---

## 6. Research Agent / Research Workflow

The system should research before it writes.

Research inputs can include:

- current themes in the target niche
- questions the audience is asking
- competitor / peer content
- recurring problems
- new technical developments
- previous GrowthOS performance data
- themes that already worked for this account

Example output:

```
Trend:
Agent harnesses / agent control layers

Why relevant:
- active discussion
- fits Eduard's technical background
- can be explained visually
- can lead naturally to GrowthOS build-in-public content

Suggested angle:
"Model vs Agent vs Harness"
```

The important point: research produces structured signals for strategy; it does not directly publish content.

---

## 7. Strategy Workflow

The Strategy step decides why content should be created, not merely what text to write.

Example:

```
Weekly objective:
Increase profile visits from a technical audience

Content mix:
- 2 educational Reels
- 1 architecture carousel
- 1 build-in-public post

Themes:
- agent harnesses
- production RAG
- GrowthOS engineering
```

Strategy should later use real performance data.

Example:

```
Observation:
Generic AI news has low retention.

Observation:
Agent architecture posts get more saves and profile visits.

Action:
Reduce generic news.
Increase architecture explainers and implementation content.
```

---

## 8. Content Planner

The planner converts strategy into a calendar.

Example:

```
Monday
Reel: Model vs Agent vs Harness

Wednesday
Carousel: 5 production RAG failure modes

Friday
Build in public: How GrowthOS creates its own content

Sunday
Short post: Engineering lesson from the week
```

Every item should support:

- Approve
- Edit
- Reject
- Regenerate
- Reschedule

---

## 9. Content Engine

GrowthOS should not use one universal prompt for everything.

Each content type should have its own workflow.

Initial content workflows:

```
Post workflow
Carousel workflow
Reel workflow
Story workflow
Article workflow
Thread workflow
```

Each workflow may have dedicated prompts, skills, constraints, QA, and channel formatting.

---

## 10. Reel Engine

The Reel Engine is a first-class workflow, not a single "generate video" call.

Target pipeline:

```
Topic
 ↓
Hook
 ↓
Script
 ↓
Storyboard
 ↓
Scenes
 ↓
Assets
 ↓
Voice
 ↓
Assembly
 ↓
Subtitles
 ↓
QA
 ↓
Approval
 ↓
Publish
```

Example:

Topic:

> Why AI agents need a harness.

Possible script structure:

```
0–3 sec
"Your AI agent doesn't need another model."

3–8 sec
"It needs control."

8–18 sec
Agent → tools → memory → policies → approvals

18–27 sec
Without this, production agents become unpredictable.

27–32 sec
That's what an agent harness solves.
```

The Creative Director workflow should then turn this into a storyboard and scene plan.

---

## 11. Media generation should be provider-agnostic

GrowthOS should not depend on one video vendor.

```
MediaProvider
├── generated video
├── generated image
├── stock media
├── screenshots
├── screen recordings
├── diagrams
├── animations
└── user-owned media
```

Possible future providers:

```
KlingProvider
VeoProvider
RunwayProvider
OtherProvider
```

The first Reel implementation does not need expensive full-AI video generation.

For a technical brand, strong Reels can be assembled from:

- animated architecture diagrams
- terminal recordings
- product UI
- screenshots
- typography
- photos
- motion graphics
- subtitles
- voiceover

Assembly can be deterministic using tools such as FFmpeg or Remotion.

This keeps costs low and avoids requiring GPU infrastructure.

---

## 12. Visual Brand Engine

GrowthOS should preserve a coherent visual identity across content.

For Eduard, a possible direction is:

```
dark
technical
minimal
clean typography
3D accents
AI systems / architecture aesthetic
```

The system should store reusable visual settings:

- palette
- fonts
- logo
- layouts
- title styles
- subtitle styles
- transitions
- Reel intro / outro
- safe zones
- reusable components

The goal is consistency, not random AI-generated visuals.

---

## 13. QA before publication

Every content workflow should have a verification step.

Reel QA examples:

```
- 9:16 format
- correct resolution
- valid duration
- audio present
- subtitles inside safe zones
- text readable
- scenes match script
- visual style consistent
- no forbidden claims
- no broken frames
```

Text QA examples:

```
- brand voice
- factual consistency
- no invented claims
- no confidential information
- no accidental duplication
- valid CTA
- valid links
```

Low-confidence output should be escalated to human review.

---

## 14. Human approval and autonomy levels

GrowthOS should not begin as an uncontrolled autonomous marketer.

Possible autonomy levels:

### Level 0
AI only proposes.

### Level 1
AI creates; human approves.

### Level 2
Approved low-risk content categories can publish automatically.

### Level 3
The system can also interact with the audience within strict policies.

The initial product should target **Level 1**.

This matches the existing GrowthOS safety principle: generate != publish.

---

## 15. Publishing layer

Publishing should use channel adapters.

```
GrowthOS
   ↓
Channel Adapter
   ↓
Instagram / LinkedIn / Telegram / ...
```

Examples:

```
InstagramChannel
LinkedInChannel
TelegramChannel
```

The core should not depend on platform-specific API details.

Where a social network restricts automation, GrowthOS should use only actions allowed by official APIs and terms.

---

## 16. Community Agent

Publishing is not the end of the workflow.

GrowthOS should eventually process comments:

```
comment
 ↓
classify
 ↓
retrieve context
 ↓
draft response
 ↓
policy check
 ↓
auto-reply OR human approval
```

Responses should use actual brand and content context.

The goal is not generic autoresponder text.

Example:

User:
> What stack did you use for this?

GrowthOS should be able to answer from the relevant project context rather than return a generic engagement message.

---

## 17. DM Agent

Where the channel officially supports it, GrowthOS can also assist with direct messages.

Message types may include:

```
spam
normal follower
technical question
recruiter
potential customer
partnership
high-value contact
```

High-value conversations should be escalated.

Example:

```
Potential lead detected

Intent:
Internal RAG platform

Confidence:
0.87

Conversation summary:
...

Suggested action:
Human takeover
```

The system should not autonomously negotiate important commercial terms.

---

## 18. Lead Engine

Marketing should connect to business outcomes.

A simple funnel:

```
Visitor
 ↓
Engaged follower
 ↓
Conversation
 ↓
Potential lead
 ↓
Qualified lead
 ↓
Human handoff
 ↓
Call
```

Example dashboard:

```
This week

3,420 impressions
212 profile visits
+37 followers
14 DMs
6 meaningful conversations
3 potential leads
1 qualified opportunity
```

This is a more meaningful product outcome than "27 posts generated."

---

## 19. Analytics

GrowthOS should measure several layers.

### Content metrics

- impressions
- reach
- video views
- watch time
- retention
- completion rate
- saves
- shares
- comments

### Profile metrics

- profile visits
- follows
- unfollows

### Conversion metrics

- website visits
- DMs
- meaningful conversations
- leads
- calls

### Operational metrics

- content items created
- rejected items
- regeneration count
- approval time
- estimated time saved

### AI/runtime metrics

- model/provider
- tokens
- estimated cost
- latency
- failures
- retries

---

## 20. Feedback loop

The feedback loop is the core differentiation.

```
Content
 ↓
Metrics
 ↓
Analysis
 ↓
Learning
 ↓
Strategy update
```

Example:

```
Observation:
Reels about agent infrastructure have 2.4× higher retention.

Observation:
Architecture posts get more saves.

Observation:
Generic AI news performs poorly.

Recommendation:
Reduce general AI-news content.
Increase engineering explainers.
```

The next content plan should be generated from those learnings.

---

## 21. Logical agent roles

GrowthOS can expose the following logical roles:

```
Orchestrator

├── Researcher
├── Strategist
├── Content Writer
├── Creative Director
├── Reel Producer
├── Publisher
├── Community Manager
├── Analyst
└── Lead Qualifier
```

Important: the MVP should **not** require nine fully autonomous agents.

Most of these can initially be deterministic workflows:

```
workflow step
→ model call
→ structured output
→ validation
→ next step
```

This is cheaper, easier to observe, and easier to make reliable than an unrestricted agent swarm.

---

## 22. GrowthOS Core Harness

The reusable technical core should eventually include:

```
GrowthOS Core

├── Runtime
├── Sessions
├── State
├── Memory
├── Skills
├── Tools
├── Providers
├── Workflows
├── Scheduler
├── Policies
├── Approvals
├── Events
├── Observability
└── Costs
```

Marketing is the first capability pack built on this core.

---

## 23. Initial skills

Possible skills/workflows:

```
research-topic
research-competitors
build-weekly-plan
write-instagram-post
create-carousel
create-reel
reply-comment
qualify-lead
analyze-performance
build-weekly-report
```

Skills should be composable but individually scoped.

---

## 24. Model-provider layer

GrowthOS should not host its own LLMs in the first version.

```
GrowthOS
 ↓
Model Router
 ├── Claude
 ├── OpenAI
 ├── Gemini
 ├── DeepSeek
 ├── OpenRouter
 └── OpenAI-compatible providers
```

The model should be a replaceable engine rather than the product itself.

Task-aware routing can later use cheaper models for simple tasks and stronger models where quality matters.

Example:

```
classification → cheap model
simple rewrite → cheap/mid model
content draft → mid model
strategy → stronger model
important DM → stronger model
```

---

## 25. BYOK (Bring Your Own Key)

A valuable commercial option is BYOK.

Users may connect their own provider accounts:

- Anthropic
- OpenAI
- OpenRouter
- Gemini
- other supported providers

In that model, the customer pays inference costs directly and GrowthOS monetizes:

- orchestration
- workflows
- integrations
- memory
- scheduling
- approvals
- analytics
- automation

This avoids turning GrowthOS into a reseller of tokens.

A managed-credit option can be considered later.

---

## 26. Policies and guardrails

Policies should be a first-class layer.

Example:

```
Never:
- invent experience
- publish unverified metrics
- reveal private information
- make unsupported legal/medical/financial claims
- negotiate pricing without approval

Auto-reply may be allowed:
- simple technical questions
- acknowledgements
- basic product questions

Human approval required:
- job offers
- commercial proposals
- pricing
- partnerships
- controversial topics
- high-value leads
```

Policies can vary by brand and channel.

---

## 27. Memory model

Do not default to putting everything in a vector database.

Different memory types:

### Brand memory
Stable facts, positioning, tone, goals, constraints.

### Content memory
What has already been published.

### Performance memory
What topics and formats perform well.

### Conversation memory
Relevant history with a person.

### Lead memory
Potential customer context and status.

### Session/workflow memory
Current execution state.

PostgreSQL can hold much of this.

Semantic/vector retrieval should be added only where it provides clear value.

---

## 28. Observability

Every meaningful model/workflow action should be traceable.

```
workflow
step
model
provider
prompt/version
input reference
output reference
tokens
cost
latency
status
error
retry
```

Example operations dashboard:

```
Today

LLM calls: 142
Estimated cost: $2.17
Posts generated: 4
Reels generated: 1
Failed jobs: 2
Average latency: ...
```

This is useful both operationally and as an engineering showcase.

---

## 29. Infrastructure

The first real deployment should run on an ordinary VPS.

No GPU is required if inference and media generation are handled by external providers.

Possible single-node deployment:

```
VPS

Docker
├── frontend
├── API
├── worker
├── scheduler
├── PostgreSQL
├── Redis
├── reverse proxy
└── monitoring
```

External services may handle:

```
LLM inference
video generation
image generation
voice generation
specialized media APIs
```

Start small. Scale only when actual usage requires it.

---

## 30. Backend direction

A pragmatic initial stack:

```
Python
FastAPI
Pydantic
PostgreSQL
Redis
background worker
scheduler
Docker
```

Avoid Kafka, Kubernetes, distributed microservices, and other infrastructure until there is evidence they are necessary.

---

## 31. Frontend / product UI

Potential top-level navigation:

```
Dashboard
Campaigns
Content
Reels
Calendar
Approvals
Channels
Inbox
Leads
Analytics
Brand
Automation
Costs
Settings
```

Example home screen:

```
Good morning, Eduard.

Today
• Reel scheduled 18:00
• 7 new comments
• 2 conversations need attention
• 1 potential lead detected

This week
Reach +42%
Profile visits +18%
Top topic: Agent Infrastructure
```

The UI should make GrowthOS feel like an operator/control center, not just a chat box.

---

## 32. Landing page

The public landing page should explain the product in seconds.

Possible positioning:

> **Your AI marketing team that actually operates.**

or:

> **AI that runs your marketing, not just writes posts.**

The core loop can be visualized directly:

```
Research
  ↓
Plan
  ↓
Create
  ↓
Publish
  ↓
Engage
  ↓
Learn
```

A polished 3D/interactive visual direction can be useful, but 3D is presentation, not product value.

Do not spend weeks on the landing page before the core loop works.

---

## 33. Live activity concept

A strong demo element is live operational activity.

Example:

```
17:21  Instagram Reel published
17:24  3 comments analyzed
17:31  Potential lead detected
17:42  Performance signal received
17:55  Next content recommendation updated
```

This immediately communicates that the system acts continuously rather than generating isolated text.

---

## 34. Eduard's personal site

In parallel, build a strong personal landing page / portfolio.

Possible structure:

```
Eduard Kharaev
AI Engineer

Build production AI systems:
- Agents
- RAG
- Multimodal AI
- AI Infrastructure
- Business Automation

Projects
Articles
GrowthOS
Contact
```

GrowthOS should become the flagship live case on the site.

The site should promote both:

- Eduard as an engineer
- GrowthOS as a product

---

## 35. Build-in-public content opportunity

The product itself can become a content engine.

Possible post/Reel themes:

- "Building an AI that manages its own Instagram"
- "I gave my AI marketing operator access to analytics"
- "This week GrowthOS changed its own content strategy"
- "How my AI decides which Reel to make next"
- "An AI handled my audience replies — here is what happened"
- "What failed when I tried to automate my marketing"

This creates a reinforcing loop:

```
build GrowthOS
→ document GrowthOS
→ publish via GrowthOS
→ attract audience
→ collect feedback
→ improve GrowthOS
```

---

## 36. Business model hypothesis

Do not begin with a fully automated SaaS funnel.

Preferred early path:

```
Eduard dogfoods GrowthOS
 ↓
real results
 ↓
people become interested
 ↓
2–3 pilot customers
 ↓
manual onboarding
 ↓
learn actual requirements
 ↓
only then productize into broader SaaS
```

Possible later pricing structure:

```
setup / onboarding fee
+
monthly subscription
+
BYOK inference
```

Pricing is not decided yet.

---

## 37. Differentiation

A generic AI content generator does this:

```
prompt
 ↓
post
```

GrowthOS should do this:

```
understand business
 ↓
research
 ↓
strategy
 ↓
plan
 ↓
create
 ↓
publish
 ↓
engage
 ↓
measure
 ↓
learn
 ↓
repeat
```

The differentiation is the operational closed loop, memory, policies, integrations, measurement, and adaptation — not simply access to an LLM.

---

## 38. Future expansion beyond marketing

The core architecture should make future packs possible.

Examples:

### Sales

```
incoming lead
→ enrichment
→ qualification
→ CRM
→ follow-up
→ human handoff
```

### Support

```
support request
→ classify
→ retrieve context
→ answer
→ verify
→ escalate if needed
```

### Recruiting

```
candidate/source
→ enrich
→ classify
→ outreach draft
→ track response
→ handoff
```

These should not be part of the initial market promise.

---

## 39. Explicit non-goals for the first version

Do **not** build yet:

- universal no-code agent builder
- autonomous swarm of many agents
- Kubernetes
- custom GPU inference cluster
- own foundation model
- full CRM
- full Ads Manager
- integrations with every social network
- complex enterprise multi-tenancy
- giant vector-memory platform
- expensive full-AI video pipeline as a prerequisite
- month-long 3D website project before product validation

These are easy ways to spend months without proving demand.

---

## 40. MVP: GrowthOS Personal Brand Operator

The first complete version should do a small number of things end-to-end.

### Required MVP capabilities

1. Store and use a Brand Profile.
2. Create a weekly content plan.
3. Create a social post.
4. Create a simple Reel.
5. Send content through an approval step.
6. Publish through supported channel adapters.
7. Collect metrics.
8. Produce a weekly analysis.
9. Feed the analysis into the next planning cycle.

The key success criterion is not feature count.

It is:

> **Can GrowthOS run a complete plan → create → approve → publish → measure → learn loop for a real account?**

---

## 41. Post-MVP expansion

After the closed loop works, add:

- comment ingestion and response workflows
- DM workflows where APIs allow it
- lead detection
- conversation memory
- policy-based auto replies
- website integration
- improved Reel/video generation
- multiple channels
- better analytics
- stronger provider/model routing

---

## 42. Target end-state experience

A mature GrowthOS session could look like:

```
Good morning, Eduard.

Yesterday's Reel
18.4K views
63% 3-sec retention
412 profile visits
76 new followers

Audience signal
Agent infrastructure is outperforming generic RAG content.

Today
✓ New Reel prepared
✓ Caption prepared
✓ Thumbnail prepared
✓ Scheduled for 19:30

Inbox
21 messages processed
3 require your attention
1 potential client detected

Estimated AI cost yesterday
$0.84
```

The user should not have to spend half a day asking:

> "What should I post today?"

---

## 43. Product definition

Working definition:

> **GrowthOS is a marketing operations harness that turns AI models, skills, tools, social integrations, memory, policies, approvals, and analytics into an AI marketing operator.**

The core hypothesis to validate is simple:

> If GrowthOS can consistently improve and operate Eduard's own marketing loop, it may become useful to other experts, founders, and small teams.

That hypothesis should be tested before broadening the product.
