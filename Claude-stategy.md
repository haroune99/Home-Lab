# The Local AI Lab — Long-Term Experiment & Content Strategy

*A public laboratory for what local AI can actually do, built on hardware you already own.*

---

## 0. The hardware reality check (read this before anything else)

You have to lead with honesty here, because your audience — if it's technical at all — will smell hype immediately.

| Device | Real role | Real ceiling |
|---|---|---|
| **MacBook Pro M2 Pro, 16GB (≈10GB usable)** | The brain of the lab | Comfortable: 3–8B models at Q4 via MLX/llama.cpp. Workable: 13–14B at Q4 if you close everything. Ugly but instructive: 20–27B at Q2/Q3 — this is a *feature* for one specific experiment below, not a general-purpose mode. Anything beyond that is a slideshow, not a demo. |
| **HP EliteBook 640 G11** | The constrained node / contrast device | No discrete GPU — you're CPU-bound. This is genuinely useful: it's your "edge device" stand-in, your second network node, and your Windows-side computer-use test bed. Don't try to make it a serious inference node; use its limitations as the point. |
| **iPhone 16 Pro** | Sensor + interface, not compute | Great camera/mic/GPS, Shortcuts automation, and enough silicon for tiny (≤3B) on-device experiments — but its real value in this lab is as a *client* that talks to the Mac over your LAN, not as a peer inference node. |
| **Oppo Find X5 Lite** | The "second-class citizen" | Mid-range Android silicon, thin on-device LLM tooling. Treat it as a dumb client/sensor. Trying to force it into a compute role will waste your time for no payoff — but it's perfect for demonstrating *model routing* and *device-aware architecture*, which is a genuinely underused content angle.

**The one-sentence version:** you don't have a GPU cluster, you have a small, deliberately heterogeneous fleet — and heterogeneity, treated honestly, is a more interesting story than horsepower. Most "local LLM" content implicitly pretends the creator has a 4090 or a Mac Studio. You don't, and saying so up front is a credibility advantage, not a weakness.

One more reality check, because it'll save you a wasted month: distributed-inference tools like **exo** are excellent, but only deliver real advantages across *multiple Apple Silicon Macs* connected over Thunderbolt 5 RDMA — a single Mac plus a non-Apple Windows laptop gets none of that benefit, and exo's Linux/non-Mac GPU support is still immature. If you want to actually pool your Mac and your HP laptop, the realistic path is **llama.cpp's RPC backend**, which abstracts inference over the network without requiring identical hardware — slower, less elegant, but it's the one that will actually work with what you own. This mismatch between the popular tool and your actual hardware is, itself, a good episode (see Idea #6).

---

## 1. What separates "cool engineering project" from "people stop scrolling"

You asked me to draw this line explicitly. Here's the rubric I used to score every idea below:

1. **The five-second test** — can someone with zero ML background understand what's impressive within 5 seconds, with the sound off? If it needs a caption explaining why it matters, it's engineering-cool, not scroll-stopping.
2. **A live number or a live face-off** — ticking token counters, side-by-side races, a visible "before/after." Static screenshots of terminal output are for GitHub, not Shorts.
3. **Violates an assumption people actually hold** — "AI needs the cloud," "AI needs a $3k GPU," "AI can't work offline," "bigger model = always better." If your experiment doesn't contradict something the average viewer believes, it won't travel.
4. **The failure is on-screen, not edited out** — your audience has seen a thousand polished demos. A model choking, a device crashing, a benchmark humbling your assumption — that's the differentiator between influencer content and lab content.
5. **It survives being explained badly by someone else** — if a friend paraphrases it secondhand and it's still interesting ("he ran two AI models against each other on a laptop and one hallucinated the whole time"), it has legs.

I'll score every flagship idea against this rubric so you can see where I think the real ceiling is.

---

## 2. The idea graveyard — what NOT to build (and why)

You explicitly asked me to be honest about overdone or weak ideas. Here's what I'd cut, because your instinct to avoid them was correct:

- **"I built a RAG chatbot over my PDFs."** Dead on arrival. It's the "hello world" of local AI content — thousands of near-identical tutorials exist. It only survives if it's a *component* of something stranger (see Idea #3), never the headline.
- **"Top 10 local LLM tools you should try."** This is listicle content, not lab content. It doesn't demonstrate anything you built or measured, and it positions you as a curator instead of an experimenter — the opposite of the identity you said you want.
- **Generic voice-assistant tutorials (Whisper + LLM + TTS).** This exact stack is now a well-worn tutorial genre — it's genuinely useful as *infrastructure* for you, but posting "I built a local voice assistant" by itself won't differentiate you. What's still fresh is proving it's *actually* offline (network capture, airplane mode, the whole nine yards) and doing something unexpected with the loop, not the stack itself.
- **Unqualified "beats ChatGPT" claims.** Audiences are numb to this and technical viewers will immediately ask for methodology. If you make a comparison claim, it needs a real, disclosed benchmark or it will cost you credibility rather than build it.
- **Prompt-engineering tips content.** Not an experiment, not reproducible, not yours — it's advice content wearing a lab coat.
- **Trying to make the Oppo phone "run a real model."** The tooling isn't there and the payoff isn't either. Use it as a client, be upfront about why, and move on — pretending otherwise is a week you won't get back.

---

## 3. The five flagship experiments

These are the projects I'd actually build the identity around. Each is scored against the rubric in Section 1.

---

### Flagship 1 — "The Council" (heterogeneous multi-agent debate across your whole fleet)

**Rubric score: cool engineering *and* stop-scrolling.** This is your signature project — the one I'd build the whole channel's reputation on.

1. **The experiment:** Distribute a panel of differently-sized/specialized local models physically across your devices — a capable generalist on the Mac, a skeptical "critic" model on the HP laptop, a retrieval agent pulling from local documents — and have them debate or collaborate on a question under a hard compute/time budget, with a judge model picking (or synthesizing) the final answer.
2. **Why it's interesting:** It's a real test of whether multi-agent debate improves accuracy over a single strong model — a genuinely open question in the field — run entirely on consumer hardware instead of a research cluster.
3. **What makes it surprising:** People assume "multi-agent AI" requires serious infrastructure. Watching a MacBook and a business laptop argue with each other over a network cable and arrive at a better answer than either alone reframes what "enough compute" means.
4. **Hardware/software:** Mac (orchestrator + strongest model via MLX), HP laptop (critic model via Ollama/llama.cpp on CPU), a simple FastAPI/HTTP layer between them, phones as optional live "audience" clients that can submit questions or watch the debate transcript stream in.
5. **Local models to use:** A ~7–8B generalist on the Mac (Qwen3 8B, Llama 3.3 8B, or Gemma-family equivalents), a smaller/faster model on the HP laptop as the adversarial critic (Phi-4-mini or a 3–4B Qwen/Gemma variant — CPU-friendly), and a separate judge pass using a different model than either debater to reduce self-preference bias.
6. **How the architecture works:** Orchestrator on the Mac sends the question to all agents in parallel, collects responses, runs a structured critique round (critic explicitly tries to find flaws), then a judge model scores and merges. Every hop is logged with latency and token cost.
7. **What you'd actually build:** A small orchestration service (Python), a real-time visualization of the debate graph (who said what, when, and why the judge picked it), and a fixed benchmark question set you re-run over time.
8. **What you could measure:** Accuracy vs. single-model baseline on a fixed eval set, wall-clock time and network overhead cost of debate vs. speed gain (if any), and how often the critic actually catches a real error vs. introduces noise.
9. **What could go wrong:** Debate can easily make answers *worse* (models talking each other out of a correct answer is a documented failure mode) — don't hide this, it's your best content if it happens on camera. Network latency between devices could dominate and make the "distributed" framing feel cosmetic rather than real.
10. **What makes a compelling post/video:** A split-screen showing both devices "thinking" in real time, with the debate transcript scrolling and a final reveal of whether the council beat the solo model — format this like a competitive game show, not a tech demo.
11. **What the final demo looks like:** A live, watchable debate with a scoreboard tracking "Council wins / Solo model wins" across a running set of questions — this is your recurring flagship format, not a one-off.
12. **Difficulty:** High. This is the most technically ambitious project on the list — real distributed orchestration, real evaluation methodology, real failure modes to debug.
13. **First prototype timeline:** 3–4 weeks for a rough two-agent version (Mac + HP laptop only, no phones yet); another 4–6 weeks to add the visualization layer and a real benchmark set.
14. **Open-source potential:** High, and genuinely useful to others — a reproducible "local multi-agent debate harness across heterogeneous consumer hardware" is not something that currently exists as a clean open project.
15. **The deeper lesson:** Real distributed-systems engineering (network orchestration, latency budgets, partial failure handling) plus a legitimate empirical contribution to the "does multi-agent debate actually help" question — this is the project that teaches you the most and is hardest to fake.

---

### Flagship 2 — "Model Fight Club" (the recurring content engine)

**Rubric score: stop-scrolling by design, and it's your cadence-keeper.** This is not your most ambitious project — it's your most *repeatable* one, and every series needs one of these to survive the gaps between big launches.

1. **The experiment:** Give the same task to models of very different sizes (e.g., a 1–3B, a 7–8B, and a heavily quantized 20B+) running side by side on the Mac, and race them live on speed, memory footprint, and a blind quality score from an independent judge model.
2. **Why it's interesting:** It turns an abstract question ("is bigger always better?") into a concrete, visual, repeatable head-to-head.
3. **What makes it surprising:** Small models winning — which happens more often than people expect on narrow tasks — directly contradicts the "just use the biggest model" instinct almost everyone has.
4. **Hardware/software:** Mac only for this one; Ollama/MLX with live token-per-second and memory telemetry piped into an on-screen overlay (a simple terminal dashboard or a lightweight web UI works).
5. **Local models to use:** Rotate weekly — small (Gemma 3/4 4B, Qwen3 4B, Phi-4-mini), mid (Qwen3 8B, Llama 3.3 8B, Mistral Small/Nemo), and a heavily quantized larger model (a 20B+ class model at Q3/Q4) to show the "does it still hold up compressed" angle.
6. **How the architecture works:** One dispatcher fires the same prompt at each model sequentially (to avoid RAM contention on 16GB), captures latency/memory/output, and a separate judge model (never one of the contestants) scores blind.
7. **What you'd actually build:** A small benchmark harness plus a simple live-overlay renderer — this is a one-time build that pays off for months of episodes.
8. **What you could measure:** Tokens/sec, peak memory, and win rate by task category (coding, reasoning, creative, factual) — build the win-rate leaderboard publicly over time, it becomes a running storyline.
9. **What could go wrong:** RAM pressure on a 16GB machine running the harness plus a model at once can cause swapping/crashes — budget for this, it's also honestly good content ("the M2 Pro tapped out here").
10. **What makes a compelling post/video:** 30–45 second cuts: prompt appears, three token counters race, judge verdict flashes — this is the format built for Shorts/TikTok specifically.
11. **What the final demo looks like:** A recurring "Model Fight Club, Episode #N" with a running leaderboard graphic that updates every post — this builds the show-identity people come back for.
12. **Difficulty:** Low-to-medium — the hard part is the harness (one-time cost), not any individual episode.
13. **First prototype timeline:** 1–2 weeks for a working harness and your first 3 episodes' worth of footage.
14. **Open-source potential:** Yes — publish the harness and the running results as a public leaderboard repo; this is exactly the kind of small, focused tool people star and fork.
15. **The deeper lesson:** Real applied benchmarking discipline — blind evaluation, avoiding self-preference judge bias, controlling for prompt sensitivity — skills that transfer directly to production AI evaluation work.

---

### Flagship 3 — "Zero Signal" (the fully offline, airplane-mode-proven assistant)

**Rubric score: stop-scrolling, if and only if you prove the offline claim on camera.** Without the proof, this collapses into the generic voice-assistant tutorial from the graveyard.

1. **The experiment:** Build a voice-driven agentic assistant — speech in, local RAG over your own documents, speech out — and prove, not claim, that it works with WiFi and cellular fully off.
2. **Why it's interesting:** "Private AI assistant" is a claim almost everyone makes and almost no one proves. You're turning a marketing claim into a verified experiment.
3. **What makes it surprising:** Watching someone put a phone in airplane mode, ask it a real question about their own files, and get a spoken, correct answer back — with a visible network monitor showing zero packets — lands as a genuine "wait, what" moment, especially for a non-technical audience who assumes all AI needs the internet.
4. **Hardware/software:** Mac runs the full pipeline — a speech-to-text model (Whisper.cpp or a comparable local STT), a local LLM for reasoning and RAG over your documents, and a local TTS engine (Kokoro or similar) for the spoken reply. iPhone acts as the mic/speaker client over your LAN (not the internet) via a Shortcut or a minimal companion app. A packet capture (Wireshark or Little Snitch) running visibly on screen is the proof mechanism.
5. **Local models to use:** A fast small-to-mid LLM for the reasoning/RAG layer (Qwen3 8B or similar, or Phi-4-mini if you want CPU-only headroom to spare), a lightweight local STT model, and a compact local TTS model — the individual components are well-trodden; the differentiator is the verification layer, not the stack.
6. **How the architecture works:** Phone captures audio on the LAN (not the open internet) → Mac transcribes → Mac runs RAG against a local document store → Mac generates a response → Mac synthesizes speech → phone plays it back. The capture tool runs the entire time and its log is the receipt.
7. **What you'd actually build:** The pipeline itself, a minimal local network bridge between phone and Mac, and — most importantly — the verification harness (a script that confirms zero external connections were made during the interaction).
8. **What you could measure:** End-to-end latency of the fully offline loop, transcription/answer accuracy against a document ground truth, and — the star metric — a literal zero in the "external packets sent" column.
9. **What could go wrong:** LAN-only communication between phone and Mac can be fiddly to set up reliably (mDNS/Bonjour quirks, firewall prompts) — expect this to eat real debugging time; also, if you get any of this wrong and something *does* phone home, that's a worse story than not attempting it, so test the capture rigorously before you film.
10. **What makes a compelling post/video:** WiFi toggle switching off on camera, a visible "0 bytes sent" counter, then a real spoken answer — this is a strong LinkedIn narrative piece (privacy-conscious professional audience) as much as a short-form visual hook.
11. **What the final demo looks like:** A single unbroken take — flip to airplane mode, ask a question about a real personal document, get a correct spoken answer, show the empty network log.
12. **Difficulty:** Medium — every individual component is well-documented; the integration and the verification proof are the real work.
13. **First prototype timeline:** 2–3 weeks for the working pipeline; add another week to build and rehearse the verification/proof layer properly.
14. **Open-source potential:** High — publish it as a reproducible "verified offline assistant" template with the packet-capture verification script included; that verification script is the part that doesn't already exist elsewhere.
15. **The deeper lesson:** Real systems-level privacy engineering — not just "run it locally" but proving data never left the device — plus practical local-network application design.

---

### Flagship 4 — "The Quantization Cliff" (the rigorous, citable benchmark project)

**Rubric score: cool engineering first, stop-scrolling second — but it's your credibility anchor.** This one won't be your biggest view-getter, but it's the project that makes technical viewers trust everything else you publish.

1. **The experiment:** Take one model and systematically degrade it across quantization levels (e.g., Q8 → Q4 → Q3 → Q2), running it against a fixed evaluation set scored by an independent judge model, to find the exact point where quality collapses rather than gracefully declines.
2. **Why it's interesting:** Most quantization content is anecdotal ("Q4 feels fine to me"). A systematic, repeatable methodology with a real dataset is a genuine (small) contribution to public knowledge, not just a demo.
3. **What makes it surprising:** Quality degradation is rarely linear — there's often a "cliff" where a model goes from usable to incoherent over one quantization step, and pinpointing exactly where that happens for a specific model/task combination is not common public data.
4. **Hardware/software:** Mac only, using llama.cpp or MLX with multiple quantized builds of the same base model, plus your Fight Club judge-scoring harness reused here.
5. **Local models to use:** Pick one well-known base model with wide quantization support (a Qwen3 or Llama 3.3 class model works well) so your results are comparable to what others are running.
6. **How the architecture works:** A test harness loops the same fixed prompt set through each quantization level, records raw outputs, and a separate un-quantized judge model (or, ideally, a panel of judges to reduce bias) scores each output against a rubric.
7. **What you'd actually build:** The benchmark harness (shareable with Fight Club), a fixed public eval set with documented task categories, and a results dataset/plot showing the collapse curve.
8. **What you could measure:** Quality score vs. quantization level, memory footprint vs. quantization level, speed vs. quantization level — and, most valuably, *where the curve bends*, not just its endpoints.
9. **What could go wrong:** Judge-model bias and prompt sensitivity can distort results if you're not careful — this is the project where methodology criticism from technical viewers is likely, so document your eval set and judging process transparently rather than hiding it.
10. **What makes a compelling post/video:** A single chart — quality collapsing off a cliff at a specific quantization level — is a strong, shareable, single-image LinkedIn/Twitter post, even without video.
11. **What the final demo looks like:** A published chart plus a downloadable eval set and harness, framed as "Experiment #00X: where does this model actually break?"
12. **Difficulty:** Medium — mechanically straightforward, but designing a *fair, defensible* eval methodology is the real work and the real value.
13. **First prototype timeline:** 2 weeks for a first pass on one model; treat later re-runs on new models as easy recurring content once the harness exists.
14. **Open-source potential:** High — a clean, reproducible quantization-quality benchmark repo with an actual dataset is genuinely useful to the broader local-LLM community and likely to get organic attention from people who cite it.
15. **The deeper lesson:** Real applied ML evaluation methodology — eval set design, judge bias, reproducibility — the exact skill set that separates "I tried a model" content from actual AI engineering.

---

### Flagship 5 — "Eyes on the Mac" (iPhone-as-sensor multimodal reasoning)

**Rubric score: stop-scrolling, easily — this is your most visually shareable single demo.**

1. **The experiment:** Stream live camera frames from the iPhone over your local network to a vision-language model running on the Mac, which reasons about what it sees and speaks a response back through the phone in near real time.
2. **Why it's interesting:** It turns your phone into the "eyes" of a system whose "brain" is a laptop in your bag — a genuinely different mental model of what a phone-based AI assistant is than the cloud-API norm.
3. **What makes it surprising:** People assume real-time multimodal reasoning needs a cloud API call to a frontier model. Watching it happen with a visible, physical tether to a laptop — with no internet involved — reframes the assumption.
4. **Hardware/software:** iPhone camera feed over LAN (a minimal companion app or an existing local-streaming approach), Mac running a compact vision-language model via MLX-VLM (or a comparable local multimodal runtime), and your Kokoro-style local TTS for the spoken response, played back through the phone.
5. **Local models to use:** A small, efficient local vision-language model sized to fit your memory budget alongside the rest of the pipeline — favor efficiency over exhaustiveness here; the goal is snappy narration, not encyclopedic description.
6. **How the architecture works:** Phone captures and streams frames on the LAN → Mac's VLM processes frames at a throttled interval (not every frame — budget this deliberately) → Mac generates a short spoken description or answer → TTS output streams back to the phone speaker.
7. **What you'd actually build:** A lightweight frame-streaming client, a throttled inference loop on the Mac (this is the actual engineering challenge — naive per-frame inference will choke your RAM budget), and the TTS playback loop.
8. **What you could measure:** End-to-end latency from "camera sees it" to "phone says it," accuracy of scene/object description against ground truth, and how throttling frequency trades off responsiveness vs. system stability.
9. **What could go wrong:** This is the most likely project to visibly strain your 16GB budget — expect stutters, dropped frames, or a need to aggressively throttle; treat that struggle as part of the story rather than something to cut around.
10. **What makes a compelling post/video:** Walking around narrating the physical world in real time through a laptop-tethered phone is inherently visual and needs almost no explanation — ideal for Shorts/TikTok/Reels.
11. **What the final demo looks like:** A short walking tour where the phone narrates its surroundings live, entirely offline, with the Mac visibly doing the work in a backpack or on a desk nearby.
12. **Difficulty:** Medium-high — real-time multimodal pipelines on constrained memory are genuinely fiddly to get smooth.
13. **First prototype timeline:** 3–4 weeks, mostly spent on throttling and latency tuning rather than the initial "does it work at all" step.
14. **Open-source potential:** Medium-high — a "phone-as-sensor, laptop-as-brain" multimodal harness is a nice, reusable template, though this category has slightly more prior art than the others.
15. **The deeper lesson:** Real multimodal systems engineering under hard memory constraints — frame throttling, latency budgeting, and the practical gap between "a VLM can do this" and "a VLM can do this smoothly on 16GB."

---

## 4. Secondary experiments (quick-hit ideas, not full flagships)

These are worth doing but don't need the full 15-point treatment — treat them as connective tissue between flagships, or as honest "myth vs. reality" episodes.

- **"I tried to build a GPU cluster from a MacBook and a Windows laptop"** — deliberately attempt the exo-style distributed-inference dream with your actual mismatched hardware, document why it doesn't deliver what the marketing implies, then show what llama.cpp's RPC backend *can* actually do across the two. This is an honest failure/reality-check story, and those consistently outperform polished ones.
- **Model routing by device capability** — build a dispatcher that classifies incoming queries and routes trivial ones to a tiny model (or even the HP laptop) while reserving the Mac's larger model for genuinely hard queries; measure the compute/time saved. Good "efficiency" narrative, and reuses your Fight Club harness.
- **Agent economics under a hard budget** — give two agents a fixed token or time budget to complete a task, competitively or cooperatively, and watch what strategies emerge (e.g., one agent front-loads a plan to avoid wasting budget on backtracking). Frame as "Hunger Games for local models" — playful, benchmarkable, and ties into your interest in constraints/competition.
- **A computer-use agent on the HP EliteBook** — worth attempting, but set expectations honestly: on CPU-only Windows hardware with a small local vision model, this will likely be slow and narrow in scope (a handful of simple, well-defined UI tasks) rather than a general "watch it use your whole OS" demo. Frame the episode around *that* honest limitation rather than overselling it — "what a local computer-use agent can and can't do on a laptop with no GPU" is itself a good, differentiated post.

---

## 5. The long-term arc

**Phase 1 — Foundation (Weeks 1–4).** Get your baseline stack solid (Ollama, MLX, llama.cpp all benchmarked and understood on your actual machine), stand up the GitHub org/repo template you'll reuse for every experiment, get the Mac and HP laptop talking over your LAN, and publish the hardware-reality-check post from Section 0 as your first piece of content — it sets audience expectations and builds early trust. Launch Model Fight Club (Flagship 2) here; it's your lowest-effort, fastest-to-publish project and keeps you posting while bigger things are in progress.

**Phase 2 — Systems (Weeks 5–12).** Build and ship Zero Signal (Flagship 3) as your first "real" flagship release — full pipeline, full verification, full open-source repo. Run the Quantization Cliff benchmark (Flagship 4) in the background during this phase; it doesn't need to be your headline content, but drip its results out as supporting posts.

**Phase 3 — Multimodal (Weeks 10–16).** Build Eyes on the Mac (Flagship 5) — your most purely visual project, good for a mid-arc engagement spike.

**Phase 4 — The signature project (Months 3–6).** Build The Council (Flagship 1). This is the most technically demanding and the one I'd bet on as your actual breakout piece — save it until your audience, your harness code, and your production process are all mature enough to do it justice.

**Ongoing.** Weave in the secondary experiments from Section 4 between flagships, keep Fight Club running on a steady cadence, and let the running leaderboard and "Experiment #NNN" numbering become the connective identity across everything — a real lab keeps a lab notebook, and yours should be public.

---

## 6. Platform strategy

| Platform | Format | What goes here |
|---|---|---|
| **YouTube Shorts / TikTok / Reels** | 30–60s, tight cuts, sound-off-readable | The 5-second-test moments: live races, the airplane-mode reveal, the walking multimodal narration. |
| **LinkedIn** | Longer text + one strong image/chart | The narrative and the lesson: what broke, what you learned, what it means for people building real systems — this is where "Zero Signal" and "Quantization Cliff" land hardest. |
| **YouTube (long-form)** | 8–15 min | The full experiment write-up: methodology, failures included, results — this doubles as documentation and is where technical credibility compounds. |
| **GitHub** | Repo per experiment, numbered | The actual receipts. Every flagship (and most secondary experiments) should ship with a reproducible repo — this is what turns viewers into a durable technical audience rather than a scroll-through one. |

---

## 7. My honest final take

If I had to pick one wedge to open the whole series with, it's **the hardware-reality-check post plus the first few Model Fight Club episodes** — cheap to produce, immediately establishes your voice (honest about constraints, rigorous about methodology), and buys you time to build The Council properly instead of rushing it. Don't lead with your most ambitious idea; lead with your most *repeatable* one, and let the flagship be the payoff once people are already watching.

The single biggest risk to this whole plan isn't technical — it's scope creep. Five flagships plus four secondary experiments plus a recurring series is a lot for one person on a 16GB laptop. If you only build three things this year, make them Zero Signal (proves the "local" claim rigorously), Model Fight Club (keeps the cadence alive), and The Council (the actual "wait, you did THAT" moment). Everything else is upside, not requirement.