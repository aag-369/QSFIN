# QSFIN Website — Master Build Prompt

**How to use this document:** this is a complete, standalone prompt. Copy everything from the
"BEGIN PROMPT" line down and paste it into Claude (or another AI website builder) to generate the
site in one shot. Everything above that line is just orientation for you.

**One assumption I made without asking you** (change this in the prompt below before using it, if
you want something different): **single-page scrolling site**, not a multi-page site with routing
— the most common and fastest-to-execute-well format for a project showcase like this.

**Your bio is now filled in with real content from your resume** (`Aayushman_ATS_Resume_726.pdf`).
Three things are still placeholders because the PDF only gave me the link *labels* ("GitHub —
LinkedIn — Portfolio"), not the actual URLs behind them — search for `[GitHub URL]`,
`[LinkedIn URL]`, and `[Portfolio URL]` in section 3H below and drop in the real links before you
use this. I deliberately left your phone number off the public bio (a personal mobile number on a
public research-project page is generally not something you want indexed by search engines) —
add it back in yourself if you actually want it public.

---

## BEGIN PROMPT

You are building a single-page, professionally designed showcase website for **QSFIN — Quantum
Sentient Forensic Intelligence Network**, a research prototype AI system for forensic
investigation and judicial decision support, built specifically to address documented gaps in
India's forensic and judicial infrastructure. Read this entire brief before writing any code —
it contains the project's real technical content, the required visual direction, the exact section
structure, and hard constraints on tone and restraint that you must not violate.

### 1. What QSFIN actually is (use this content — do not invent different facts)

QSFIN is a working prototype (not a shipped product, not a company) that takes a crime scene
through an AI-assisted pipeline in five stages:

1. **Digital Twin** — a persistent, queryable 3D reconstruction of a crime scene (rooms, evidence
   markers, ballistic trajectories, chain-of-custody records), built from structured scan data.
   Replaces static photographs with an explorable, permanent virtual scene.
2. **Multi-Agent Forensic Analysis** — four specialized, narrow AI agents (Ballistics &amp; Trace
   Evidence, Digital Forensics, Network Analysis, Timeline Reconstruction) that each independently
   analyze one slice of the case and post structured, confidence-scored findings to a shared
   blackboard — mirroring how a real investigative team is organized, and keeping every
   sub-conclusion auditable in isolation.
3. **Neuro-Symbolic Explainable Reasoning** — a reasoning layer that keeps two things visibly
   separate: a statistical aggregation of all agent findings ("the neural part"), and a small set
   of explicit, named, human-readable rules that adjust that score ("the symbolic part") — e.g.
   discounting evidence with a broken chain of custody. Every ranking comes with a full,
   plain-language explanation chain, because a black-box confidence score is not admissible or
   persuasive in a courtroom — a traceable reasoning chain is.
4. **Quantum-Inspired Scenario Optimization** — competing scenarios and contested evidence are
   jointly formulated as a QUBO (Quadratic Unconstrained Binary Optimization) problem — the same
   mathematical form used by real quantum annealers and QAOA circuits — and solved via simulated
   annealing, verified against an exact brute-force optimum. **Be precise and honest about this on
   the site: this runs on classical hardware today, using quantum-inspired mathematics, and is
   built to be quantum-ready as real quantum hardware matures. Never claim or imply a working
   quantum computer is involved.**
5. **Federated Learning Across Agencies** — a simulation of multiple police/forensic agencies each
   training a local model on their own case data, combined via FedAvg (federated averaging) into a
   shared model — without any agency's raw case data ever leaving that agency. Demonstrated result:
   federated accuracy (~84.1%) lands close to a fully-centralized-data ceiling (~84.3%), both above
   local-only performance (~83.2%) — proof the approach works without pooling sensitive data.

**Why this matters for India specifically** (use these real, cited statistics — do not soften or
round them into vague claims):
- Roughly **50% of sanctioned scientific posts in India's forensic science laboratories are
  vacant** nationwide; in Telangana's FSL, scientific-staff vacancy reaches **91%**.
- Key forensic disciplines (DNA analysis, toxicology, biology, cyber forensics) run at
  **4–5× their sanctioned workload capacity**.
- **Over 5 crore cases are pending** across the Indian judicial system; **76% of all prisoners are
  undertrials** — not yet convicted.
- National prison occupancy averages **131%** (some facilities over 400%).
- The BNSS (2024) now legally mandates forensic investigation for serious offences, with states
  given until roughly **2029** to fully comply — because the infrastructure doesn't yet exist.
- Forensic evidence is frequently **rejected or weakened in Indian courts** specifically because
  chain-of-custody and methodology can't be adequately demonstrated — the exact gap QSFIN's
  explainability layer targets.

**Critical tone requirement:** QSFIN is a research prototype running entirely on **synthetic,
fictional demonstration data** — no real case, person, or agency. The site must never imply this is
a deployed system, a company, or that it has processed real cases. It should read as a serious,
credible research project — ambitious but honest about what's simulated vs. what a real deployment
would require. Confidence without exaggeration. This honesty is a *feature* of the site's voice,
not a disclaimer to hide in fine print — work a brief, tasteful "prototype / synthetic data" signal
into the hero area itself, not just the footer.

### 2. Visual identity & theme — "forensic lab meets quantum lab"

The theme must fuse two visual worlds without looking like a Halloween costume of either one:
**forensic/criminal investigation** (evidence tags, case files, chain-of-custody, scene
reconstruction, ballistics trajectories, redaction marks, dossier typography) and **quantum
computing** (qubits, superposition/entanglement motifs, circuit diagrams, energy-landscape/
optimization surfaces, node-and-edge graphs). The synthesis should feel like a **classified
research lab briefing** — restrained, dark, precise, slightly clinical — not like a crime thriller
poster and not like a generic SaaS product page.

**Non-negotiable constraint: this must read as extremely professional and minimal, not busy.**
Every motif below is something to use *sparingly, as accent texture*, never as decoration that
competes with content. If in doubt, cut it. A hiring manager, a professor, or a government
official should look at this site and think "serious research," never "student project with
effects."

**Color system** (dark-mode-first; use these as CSS custom properties, do not invent extra hues):

```
--bg-void:        #06080d   /* page background, near-black with a cold blue cast */
--bg-surface:     #0d1119   /* card / panel surface */
--bg-surface-2:   #131826   /* nested / hovered surface */
--border-hairline:rgba(255,255,255,0.08)
--ink-primary:    #f2f4f8   /* headings, primary text */
--ink-secondary:  #a7b0c0   /* body copy */
--ink-muted:      #5c6577   /* captions, meta, timestamps */
--accent-quantum: #3ea6ff   /* electric blue — quantum/tech elements, links, primary CTA */
--accent-quantum-dim: #1c4d7a
--accent-forensic:#e0483e   /* evidence red — used ONLY for evidence markers, alerts, key highlights — never decoratively */
--accent-amber:   #d9a441   /* case-file amber — used ONLY for "flagged/pending" states, sparingly */
--success:        #34c77b   /* used ONLY for verified/confirmed states */
--grid-line:       rgba(62,166,255,0.08)  /* faint circuit/blueprint grid texture */
```

Rules: this is fundamentally a **near-monochrome dark palette with exactly one dominant accent
(quantum blue)** and two *reserved-meaning* accents (forensic red for evidence/critical, amber for
flagged/pending). Red and amber are never used decoratively — only when they mean "evidence
marker" or "needs review," exactly like the actual dashboard this project already ships. Do not
introduce a rainbow of section-by-section colors. Consistency across the whole page is what makes
it read as professional rather than a portfolio grab-bag.

**Typography:**
- A clean, technical sans-serif for all UI and body text (system stack: `-apple-system,
  "Segoe UI", "Inter", Roboto, sans-serif`, or self-host **Inter**).
- A monospace face (`"JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace`) used
  *deliberately and sparingly* for: case IDs, evidence IDs, code/data snippets, stat labels,
  timestamps, the QUBO/energy values — anywhere the content is literally data or an identifier.
  This is the single strongest tool for making the site feel like a real forensic/technical system
  rather than a marketing page. Do not use monospace for headings or body prose.
- Tight, confident type scale. Large hero headline (clamp between ~40px mobile and ~76px desktop),
  clear hierarchy, generous line-height on body copy (1.6–1.7), generous letter-spacing on
  eyebrow/label text (uppercase, 11–12px, +0.08em tracking).

**Texture & motif system** (use at low opacity, as background/ambient detail — never as
foreground decoration):
- A faint **blueprint/circuit grid** (1px lines, `--grid-line`) behind hero and section
  backgrounds — evokes both forensic scene-diagramming and quantum circuit diagrams at once.
- **Scanline / HUD accents**: thin animated horizontal line sweeping very slowly across the hero
  on load (like a document scanner or LiDAR sweep) — subtle, one-time or very slow loop, never
  distracting, easy to disable via `prefers-reduced-motion`.
- **Evidence-tag / dossier chips**: small monospace pill labels (e.g. `EVIDENCE E-02`,
  `CASE QSFIN-2026-0417`, `STATUS: SYNTHETIC DEMO`) used as section eyebrows or stat labels —
  ties directly back to the real system's own UI language.
- **Node/graph line art**: thin connecting lines between related concept nodes (e.g. in the "how
  it works" pipeline, or the multi-agent section) — echoes both a criminal network graph and a
  quantum qubit-connectivity diagram. Render in SVG, animate connections drawing in on scroll.
- **Redaction-bar accents**: an occasional thin black/dark bar with rounded ends, used purely as a
  graphic underline or divider element (never actually redacting real content) — a nod to case-file
  documents.
- Absolutely avoid: neon/cyberpunk clichés (glitch text, excessive glow, matrix rain), stock crime
  imagery (magnifying glasses over red string, chalk body outlines, handcuffs), and generic AI
  clichés (glowing brains, robot hands). This is a serious systems-engineering project, not a video
  game.

### 3. Site structure — single scrolling page, anchored sections, sticky nav

Build ONE page with a fixed/sticky slim top navigation bar (logo mark + wordmark on the left,
anchor links to each major section on the right, collapsing to a hamburger on mobile) that
smooth-scrolls to sections and highlights the active section as the user scrolls. Sections, in
order:

**A. Hero**
- Eyebrow label (monospace pill): `RESEARCH PROTOTYPE · SYNTHETIC DEMONSTRATION DATA`
- Headline: the project name treated as a wordmark — "QSFIN" large, with "Quantum Sentient
  Forensic Intelligence Network" as a smaller subhead line beneath it.
- One or two sentences of plain-English positioning (not jargon) — something like: an AI system
  that reconstructs crime scenes, reasons about competing theories with full explainability, and
  helps close India's forensic-capacity gap — pulled from the plain-English framing already
  developed for this project, not reworded into marketing fluff.
- Two CTAs: primary ("Explore the system" → scrolls to pipeline section) and secondary ("View
  the live dashboard" → links out to / embeds the actual dashboard artifact).
- Background: the faint blueprint grid + slow scanline sweep described above. Optionally a subtle
  animated node-graph in the far background (very low opacity, decorative only).
- A row of 3–4 small stat tiles under the fold using the REAL India statistics above (e.g. "50%
  forensic posts vacant", "5+ crore pending cases", "76% undertrials") in monospace numerals with
  small caption labels — this immediately establishes stakes without a wall of text.

**B. The Problem (India's forensic gap)**
- Concise section making the case for *why*, using the cited statistics as the backbone. Consider
  a horizontal bar or stat-grid layout (reuse the dataviz-skill-appropriate approach: single
  accent hue, clear labels, no chart-junk) rather than a wall of paragraphs.
- End with the specific, human-readable gap statement: no existing Indian system combines scene
  reconstruction + multi-agency intelligence + court-ready explainable reasoning.

**C. How It Works — the five-stage pipeline**
- The centerpiece interactive section. Present the five stages (Digital Twin → Multi-Agent
  Analysis → Neuro-Symbolic Reasoning → Quantum-Inspired Optimization → Federated Learning) as a
  horizontal (desktop) / vertical (mobile) connected pipeline with numbered nodes and animated
  connecting lines that draw in on scroll (IntersectionObserver-driven).
- Each stage is a clickable/expandable card: collapsed state shows icon + stage name + one-line
  description; expanded state reveals the fuller explanation (content from section 1 above),
  a small supporting visual (see interactive elements below), and — where relevant — a real
  number from the prototype (e.g. "14 findings across 4 agents", "verified against exact
  brute-force optimum", "84.1% federated accuracy").
- This section should make the *mechanism* legible to a non-technical visitor (a reviewer, a
  government official, a professor) in under two minutes of scrolling, while still satisfying a
  technical visitor who expands every card.

**D. Explainability in Action — a worked example**
- A focused showcase of the neuro-symbolic reasoning layer's actual output style: show one
  abbreviated real-format example (scenario ranking with raw vs. adjusted score, one or two
  finding bullets with agent + confidence + reasoning, one symbolic rule firing with its plain-
  language justification) styled as an evidence dossier / case-file card. This is the section that
  proves the "explainable, court-ready" claim rather than just asserting it.
- Use monospace for scores/IDs, sans-serif for the reasoning prose, a subtle left border in
  `--accent-quantum` on "supports" lines and `--accent-forensic` on "contradicts" lines (exactly
  mirroring the real dashboard's visual language — do not invent a different encoding).

**E. Live Demo**
- An embed (iframe) of the actual QSFIN dashboard artifact if a URL/path is available, or, if
  embedding isn't feasible, a high-quality static screenshot carousel/tabs (Overview / Digital
  Twin / Agent Findings / Reasoning / Optimization / Federated Learning — the six real dashboard
  tabs) with a clear "Open full interactive dashboard" button linking out.
- Caption clearly: "Running on synthetic demonstration data."

**F. The Five Research Threads**
- A clean grid (2–3 columns desktop, 1 column mobile) of the five publishable sub-projects
  (Digital Twin Reconstruction, Multi-Agent Reasoning Framework, Explainable AI for Legal
  Reasoning, Federated Learning Across Agencies, Quantum-Inspired Graph Optimization), each as a
  card with a one-line description and a "status" chip (e.g. "Prototype implemented",
  "Simulated at demo scale") — communicates the project's honest maturity level per-thread instead
  of one blanket claim for the whole system.

**G. Roadmap**
- A simple horizontal or vertical timeline/stepper (not a gimmicky animated timeline — restrained)
  showing the realistic extension path: real capture pipeline → trained-model agents → legal
  validation of explanations → real quantum-hardware benchmarking → real multi-agency federated
  deployment. Pulled from the project's actual architecture roadmap, not invented milestones.

**H. About the Creator**
- A focused, uncluttered bio card/section — photo (or a placeholder), name, title/role, a short
  bio paragraph, a skills/focus-area strip, and social/contact links. Use this exact content
  (real, drawn from the creator's resume — only the three bracketed URL fields still need filling
  in; do not alter or invent anything else in this block):

  ```
  Name / display name:   Aayushman Ghatak
  Title / role:          B.Tech CSE (AI & ML) Undergraduate, SRM Institute of Science and Technology
  Location:               Chennai, Tamil Nadu, India
  One-line tagline:       Building secure, production-oriented AI systems at the intersection of
                          machine learning, cybersecurity, and quantum computing.
  Bio paragraph:          Aayushman Ghatak is a Computer Science (AI & ML) undergraduate at SRM
                          Institute of Science and Technology, specializing in applied AI, computer
                          vision, cybersecurity, and quantum computing. His work spans deep learning
                          for industrial and medical inspection (VisiReport AI, a computer-vision
                          pipeline for autonomous medical PCBA inspection), quantum-integrated IoT
                          security (Fusion Gate, combining GRU-based anomaly detection with
                          Qiskit-driven adaptive cryptographic switching based on Quantum Bit Error
                          Rate), and hands-on offensive security as a Cyber Security Engineer Intern
                          at Mindenious, conducting black-box penetration testing with Burp Suite and
                          sqlmap. He previously served as Chairperson of the IEEE GRSS SRM Student
                          Chapter, leading multidisciplinary technical teams on AI research
                          initiatives. QSFIN grew directly out of this combination of interests —
                          AI systems built to hold up under adversarial scrutiny, whether that
                          scrutiny comes from a penetration test or a court of law.
  Focus-area chips:       Applied AI · Computer Vision · Cybersecurity & Pentesting · Quantum
                          Computing (Qiskit) · Quantum Cryptography & QKD
  Profile photo:          [image path/URL, or omit and use a monogram "AG" avatar instead]
  Email:                  aayushmanghatakofficial@gmail.com
  GitHub:                 [GitHub URL]
  LinkedIn:               [LinkedIn URL]
  Portfolio:               [Portfolio URL]
  ```

  Design this section with the same restraint as everything else: a clean two-column layout
  (photo/avatar left, bio + links right, on desktop; stacked on mobile), no glowing frames, no
  extraneous icons beyond simple link icons for GitHub/LinkedIn/email/portfolio. Render the
  focus-area chips as small monospace pills consistent with the evidence-tag chip style used
  elsewhere on the site (section 2) — it's a natural, on-theme way to surface the skills strip
  without a generic "skills list." For the three still-bracketed URL fields, render obviously
  editable placeholder buttons (e.g. a dashed-border pill reading "Add GitHub URL") rather than
  broken links or silently omitted buttons — the site owner must not be able to publish without
  noticing they need to fill these in.

**I. Footer**
- Compact: project name/wordmark, one-line description, the synthetic-data disclosure repeated
  once more plainly, links (dashboard, source/GitHub if applicable, contact), and a copyright line
  with the creator's name.

### 4. Interactivity requirements (all must degrade gracefully — nothing should be required for
the content to be readable with JavaScript disabled or reduced-motion enabled)

- **Scroll-triggered reveal animations** on section entry (fade + slight upward translate,
  ~400–600ms, staggered for grouped items) via IntersectionObserver — subtle, not bouncy.
- **Sticky nav with active-section highlighting** as described above.
- **Animated stat counters**: numeric stats (50%, 5+ crore, 76%, 84.1%, etc.) count up from 0 when
  they scroll into view, once, over ~800ms–1.2s. Never re-trigger on every scroll pass.
- **Expand/collapse pipeline stage cards** (section C) with smooth height transitions.
- **Animated SVG connector lines** that draw themselves in (stroke-dashoffset technique) as the
  pipeline section scrolls into view.
- **Tabbed demo screenshots/embed** (section E) with keyboard-accessible tab controls.
- **Hover states everywhere interactive**: subtle brightness/border shift on cards and buttons,
  no scale/skew gimmicks, transition ≤200ms.
- **A working dark/light toggle is optional and not required** — the project's real dashboard is
  dark-only and that's an intentional, coherent choice; if you add a light mode, it must be a
  fully separate validated palette, not an automatic filter-invert.
- **Respect `prefers-reduced-motion`**: disable/shorten all scroll animations, counters resolve
  instantly, the scanline sweep is removed entirely.
- Every animation must have a clear *reason* tied to content (revealing information, showing
  connection, showing progress) — reject any effect that exists only to look impressive. This is
  the single most important interactivity rule for keeping the site "professional, not flashy."

### 5. Technical requirements

- **Stack**: a single self-contained HTML file (inline CSS + JS, no build step) is preferred for
  portability and easy hosting anywhere — OR a lightweight React + Tailwind setup if the target
  environment expects a component-based project. Default to the single-file approach unless you
  have a specific reason to need componentization.
- **No backend required** — everything is static content plus client-side interactivity; the "live
  demo" is either an iframe embed of an already-built artifact or static screenshots.
- **Fully responsive**: mobile-first breakpoints, test the pipeline/graph sections specifically at
  narrow widths since they're the most layout-complex.
- **Accessible**: semantic HTML landmarks, proper heading hierarchy (one H1, logical H2/H3
  nesting), sufficient color contrast (verify text on `--bg-void`/`--bg-surface` against WCAG AA —
  `--ink-secondary` and darker must not be used for body text below 14px), all interactive
  elements keyboard-reachable and focus-visible, meaningful alt text on any real imagery,
  `aria-expanded` on collapsible cards, `aria-current` on active nav link.
- **Performance**: no heavy animation libraries required — plain CSS transitions/keyframes and
  vanilla JS IntersectionObserver are sufficient and keep the page light. If a 3D/graph library is
  used for a decorative background, lazy-load it and cap its impact; never let decorative visuals
  block content rendering.
- **SEO/meta**: descriptive `<title>`, meta description summarizing QSFIN in one sentence, Open
  Graph tags (title, description, a representative image — e.g. a dashboard screenshot) for clean
  link previews when shared.
- **No placeholder lorem ipsum anywhere** — every piece of body content should either come from
  section 1 of this brief or be an explicitly-marked bracketed placeholder as specified in section
  3H. A polished layout with fake filler text is worse than an honest gap.

### 6. Definition of done — check before declaring the site complete

- [ ] Every stat and technical claim on the page traces back to real content from this brief — none
      invented, none rounded away from precision (e.g. "91% vacancy in Telangana" stays specific,
      not softened to "high vacancy").
- [ ] The quantum-optimization section explicitly and clearly states this runs on classical
      hardware today via quantum-inspired methods — never implies real quantum hardware.
- [ ] The synthetic-data / prototype status is visible in the hero, not just the footer.
- [ ] Color palette matches section 2 exactly — one dominant accent, two reserved-meaning accents,
      no rainbow of section colors.
- [ ] The About/Creator section either has your real details filled in, or has clearly-marked,
      visually obvious placeholders — never invented biographical content.
- [ ] Every animation is reveal/progress-driven, none are decoration-only; `prefers-reduced-motion`
      is respected throughout.
- [ ] Fully readable and navigable with JavaScript disabled (content present in DOM, just without
      the motion/counters).
- [ ] Passes a basic contrast check for all body text against its background.
- [ ] Looks, on a first five-second glance, like a serious research lab's project page — not a
      hackathon demo, not a sci-fi movie poster, not a generic SaaS landing page.

## END PROMPT
