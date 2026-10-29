const pptxgen = require("pptxgenjs");
// Requires: npm install pptxgenjs. applyTheme comes from Anthropic's pptx skill; if absent, theme colours fall back to Office defaults.
let applyTheme = async () => {};
try { ({ applyTheme } = require("./apply_theme.js")); } catch (e) { console.warn("apply_theme.js not found: skipping theme colours"); }

const THEME = {
  name: "FedGDBD Navy Teal",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "22262E", lt1: "FFFFFF", dk2: "1E2A4A", lt2: "E7EAF3",
    accent1: "1C7293", accent2: "5B6478", accent3: "DFEDF0", accent4: "D8DCE4",
    accent5: "9AA6BF", accent6: "CBD6EE", hlink: "1C7293", folHlink: "5B6478",
  },
};
const HEX = { navy: "1E2A4A", teal: "1C7293", slate: "5B6478", border: "D8DCE4", ice: "CBD6EE", muted: "9AA6BF" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Reproducing Fed-GDBD";
pres.author = "D Maithreya, Maharshi Kundu, Siddhanth R Naik";
const C = pres.SchemeColor;

const NAVY = C.text2, TEAL = C.accent1, SLATE = C.accent2, TINT_T = C.accent3, BORDER = C.accent4,
  MUTED = C.accent5, TINT = C.background2, DARK = C.text1, WHITE = C.background1, ICE = C.accent6;
const MONO = "Courier New";

// ---------------- Layouts ----------------
pres.defineSlideMaster({
  title: "DARK",
  background: { color: NAVY },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: WHITE },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.5, y: 0.28, w: 9, h: 0.25, fontSize: 9, bold: true, color: TEAL, charSpacing: 1, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.52, w: 9, h: 0.55, fontFace: "Cambria", fontSize: 24, bold: true, color: NAVY, margin: 0, valign: "middle", align: "left" }, text: "" } },
    { placeholder: { options: { name: "footer", type: "body", x: 0.5, y: 5.25, w: 6, h: 0.22, fontSize: 8, color: MUTED, margin: 0, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 9.0, y: 5.25, w: 0.5, h: 0.22, fontSize: 8, color: MUTED, align: "right", margin: 0 },
});

// ---------------- Helpers ----------------
function content(section, kicker, title, footer) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  s.addText(footer, { placeholder: "footer" });
  return s;
}
function card(s, x, y, w, h, fill = TINT, line = BORDER, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: fill }, line: { color: line, width: 0.75 }, objectName: name });
}
function txt(s, text, o) {
  s.addText(text, Object.assign({ isTextBox: true, margin: 0, valign: "top", fontSize: 12, color: DARK }, o));
}
function num(s, n, x, y, d = 0.32, fill = NAVY) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  s.addText(String(n), { isTextBox: true, x, y, w: d, h: d, align: "center", valign: "middle", fontSize: 11, bold: true, color: WHITE, margin: 0 });
}
function code(s, lines, x, y, w, h, fs = 10.5) {
  card(s, x, y, w, h, NAVY, NAVY);
  s.addText(lines.join("\n"), { isTextBox: true, x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, fontFace: MONO, fontSize: fs, color: WHITE, margin: 0, valign: "top", paraSpaceAfter: 0 });
}
function tbd(s, x, y, w, h, label) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: WHITE }, line: { color: TEAL, width: 1, dashType: "dash" } });
  s.addText(label, { isTextBox: true, x: x + 0.2, y, w: w - 0.4, h, align: "center", valign: "middle", fontSize: 11, italic: true, color: TEAL, margin: 0 });
}

// =====================================================================
// 1. Title
// =====================================================================
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Introduction" });
  txt(s, "IT307 · MACHINE LEARNING  —  PROJECT PRESENTATION", { x: 0.6, y: 0.55, w: 8.8, h: 0.25, fontSize: 9, bold: true, color: ICE, charSpacing: 1 });
  txt(s, "Reproducing Fed-GDBD: Global Decision Boundary Distillation for Heterogeneous Federated Learning", { x: 0.6, y: 0.9, w: 8.6, h: 1.3, fontFace: "Cambria", fontSize: 26, bold: true, color: WHITE, valign: "middle" });
  txt(s, "An independent re-implementation of Zhang et al. (JKSU-CIS, 2025), evaluated on CIFAR-10 and CIFAR-100 with 20 clients and four different model architectures", { x: 0.6, y: 2.45, w: 8.4, h: 0.6, fontSize: 13, italic: true, color: ICE });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 3.25, w: 8.8, h: 1.6, rectRadius: 0.06, fill: { color: "2C3B63" }, line: { color: "2C3B63" } });
  const team = [["D Maithreya", "241AI013"], ["Maharshi Kundu", "241AI022"], ["Siddhanth R Naik", "241AI040"]];
  team.forEach(([n, r], i) => {
    txt(s, n, { x: 0.85 + i * 2.9, y: 3.45, w: 2.7, h: 0.3, fontSize: 14, bold: true, color: WHITE });
    txt(s, r, { x: 0.85 + i * 2.9, y: 3.75, w: 2.7, h: 0.25, fontSize: 11, color: ICE });
  });
  txt(s, "Instructor: Dr. Nagamma Patil", { x: 0.85, y: 4.2, w: 8, h: 0.25, fontSize: 11, color: WHITE });
  txt(s, "National Institute of Technology Karnataka, Surathkal", { x: 0.85, y: 4.45, w: 8, h: 0.25, fontSize: 11, color: ICE });
  s.addNotes("Introduce the team and the goal: we did not just read the paper, we re-implemented Fed-GDBD from scratch because the authors did not release code, and ran it against two baselines on two datasets.");
}

// =====================================================================
// 2. Introduction
// =====================================================================
{
  const s = content("Introduction", "INTRODUCTION", "What We Set Out to Do", "INTRODUCTION");
  txt(s, [
    { text: "Heterogeneous federated learning (HtFL). ", options: { bold: true, color: NAVY } },
    { text: "Clients train together without sharing raw data, while holding non-IID data and running different model architectures, so FedAvg-style weight averaging is impossible.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "The paper. ", options: { bold: true, color: NAVY } },
    { text: "Fed-GDBD (Zhang et al., 2025) shares clustered class prototypes and distils a server-trained global decision boundary back into every client.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Our goal. ", options: { bold: true, color: NAVY } },
    { text: "Re-implement Fed-GDBD (no official code exists) and test its headline claim: that it beats prototype-sharing and classifier-sharing baselines under strong label skew." },
  ], { x: 0.5, y: 1.35, w: 4.6, h: 3.0, fontSize: 13 });

  const stats = [["20", "clients, all participating each round"], ["4", "architectures: CNN, GoogLeNet, MobileNetV2, ResNet18"], ["2", "datasets: CIFAR-10 and CIFAR-100"], ["3+1", "methods: Fed-GDBD, FedProto, LG-FedAvg + our FedGDBD-S"]];
  stats.forEach(([n, l], i) => {
    const x = 5.5 + (i % 2) * 2.05, y = 1.35 + Math.floor(i / 2) * 1.5;
    card(s, x, y, 1.9, 1.35);
    txt(s, n, { x: x + 0.15, y: y + 0.12, w: 1.6, h: 0.6, fontFace: "Cambria", fontSize: 32, bold: true, color: TEAL, valign: "middle" });
    txt(s, l, { x: x + 0.15, y: y + 0.72, w: 1.65, h: 0.55, fontSize: 10, color: SLATE });
  });
  card(s, 0.5, 4.45, 4.6, 0.6, TINT_T, TINT_T);
  txt(s, [{ text: "Two challenges at once: ", options: { bold: true, color: NAVY } }, { text: "label skew Dir(β = 0.1) and model heterogeneity" }], { x: 0.65, y: 4.45, w: 4.3, h: 0.6, fontSize: 11, valign: "middle" });
  s.addNotes("HtFL has two problems at once. Data heterogeneity: with a Dirichlet split at beta 0.1, many clients see only a few classes. Model heterogeneity: each client runs one of four architectures, so parameters cannot be averaged. Fed-GDBD claims to handle both. We re-implemented it and compared against two baselines.");
}

// =====================================================================
// 3. Literature survey
// =====================================================================
pres.addSection({ title: "Literature Survey" });
{
  const s = content("Literature Survey", "LITERATURE SURVEY", "Where Fed-GDBD Fits in HtFL Research", "LITERATURE SURVEY");
  const cols = [
    ["Public-data distillation", "FedMD · FedDF · KT-pFL", "Clients exchange logits on a shared public dataset. Quality depends on how relevant that public data is, and one may not exist.", "Not compared (needs public data)"],
    ["Global classifier sharing", "LG-FedAvg (2020) · FedGH (2023)", "Clients keep private feature extractors and average or share only the classifier head. One head must fit very different feature spaces.", "Baseline: LG-FedAvg"],
    ["Prototype sharing", "FedProto (2022) · FedTGP (2024)", "Clients send per-class mean features; the server averages them. A single averaged prototype per class drifts away from every client's true class centre.", "Baseline: FedProto"],
  ];
  cols.forEach(([h, m, b, tag], i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 1.3, 2.85, 2.55);
    txt(s, h, { x: x + 0.18, y: 1.45, w: 2.5, h: 0.3, fontSize: 13, bold: true, color: NAVY });
    txt(s, m, { x: x + 0.18, y: 1.75, w: 2.5, h: 0.25, fontSize: 10, color: TEAL, bold: true });
    txt(s, b, { x: x + 0.18, y: 2.08, w: 2.5, h: 1.25, fontSize: 11, color: SLATE });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.18, y: 3.38, w: 2.5, h: 0.32, rectRadius: 0.05, fill: { color: i === 0 ? WHITE : NAVY }, line: { color: i === 0 ? BORDER : NAVY } });
    txt(s, tag, { x: x + 0.18, y: 3.38, w: 2.5, h: 0.32, fontSize: 10, bold: true, color: i === 0 ? SLATE : WHITE, align: "center", valign: "middle" });
  });
  card(s, 0.5, 4.05, 9.0, 0.8, TINT_T, TINT_T);
  txt(s, [
    { text: "Fed-GDBD combines both ideas: ", options: { bold: true, color: NAVY } },
    { text: "several k-means++ prototypes per class (not one mean) train a server-side classifier g, which is then used as a distillation teacher rather than copied into clients. Irrelevant-class KD reduces forgetting." },
  ], { x: 0.7, y: 4.05, w: 8.6, h: 0.8, fontSize: 12, valign: "middle" });
  s.addNotes("Three families. Public-data distillation needs a public dataset, so it is out of scope. Classifier sharing, like LG-FedAvg, forces one head onto different feature spaces. Prototype sharing, like FedProto, averages a single prototype per class. We picked one representative from each of the last two families as our baselines. Fed-GDBD sits between them: multiple prototypes train a global classifier, which is used as a teacher.");
}

// =====================================================================
// 4. Methodology: pipeline
// =====================================================================
pres.addSection({ title: "Proposed Methodology" });
{
  const s = content("Proposed Methodology", "PROPOSED METHODOLOGY · PIPELINE", "One Communication Round of Fed-GDBD", "PROPOSED METHODOLOGY");
  card(s, 0.5, 1.25, 9.0, 0.5, TINT, BORDER);
  txt(s, [{ text: "Round 0 (once): ", options: { bold: true, color: NAVY } }, { text: "clients pre-train with cross-entropy → server sets g = sample-weighted average of client heads (Eq. 5)" }], { x: 0.68, y: 1.25, w: 8.7, h: 0.5, fontSize: 11, valign: "middle" });

  const steps = [
    ["Local training", "CE + T²·IKD from the client's best past model (Eq. 11)", "client"],
    ["Multi-prototype clustering", "k-means++ on features f(x), v = 5 prototypes per class (Eq. 3–4)", "client"],
    ["Train global learner g", "Server pools all prototypes Pᵍ and trains g with CE (Eq. 12)", "server"],
    ["Broadcast g", "g = Linear(512 → C), same shape as every client head", "server"],
    ["Boundary distillation", "(1−α)·CE + α·T²·KL(g ‖ h) on local data (Eq. 13)", "client"],
  ];
  const w = 1.64, gap = 0.2, y = 2.05, h = 1.95;
  steps.forEach(([t, d, who], i) => {
    const x = 0.5 + i * (w + gap);
    const srv = who === "server";
    card(s, x, y, w, h, srv ? NAVY : TINT_T, srv ? NAVY : TINT_T);
    num(s, i + 1, x + 0.15, y + 0.15, 0.32, srv ? TEAL : NAVY);
    txt(s, t, { x: x + 0.15, y: y + 0.55, w: w - 0.3, h: 0.5, fontSize: 12, bold: true, color: srv ? WHITE : NAVY });
    txt(s, d, { x: x + 0.15, y: y + 1.05, w: w - 0.25, h: 0.85, fontSize: 10, color: srv ? ICE : SLATE });
    if (i < steps.length - 1) s.addShape(pres.shapes.ISOSCELES_TRIANGLE, { x: x + w + 0.02, y: y + h / 2 - 0.06, w: 0.16, h: 0.12, fill: { color: MUTED }, line: { color: MUTED }, rotate: 90 });
  });
  // legend + comms
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 4.3, w: 0.22, h: 0.18, rectRadius: 0.03, fill: { color: TINT_T }, line: { color: TINT_T } });
  txt(s, "client side", { x: 0.8, y: 4.27, w: 1.2, h: 0.25, fontSize: 10, color: SLATE });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.9, y: 4.3, w: 0.22, h: 0.18, rectRadius: 0.03, fill: { color: NAVY }, line: { color: NAVY } });
  txt(s, "server side", { x: 2.2, y: 4.27, w: 1.2, h: 0.25, fontSize: 10, color: SLATE });
  txt(s, [
    { text: "Communicated per round: ", options: { bold: true, color: NAVY } },
    { text: "up = prototypes only (v × classes × 512 floats, a few KB);  down = g (512·C + C weights). Raw data and feature-extractor weights never leave the client." },
  ], { x: 0.5, y: 4.6, w: 9.0, h: 0.5, fontSize: 11 });
  s.addNotes("Walk through one round. Steps 1, 2 and 5 run on every client, 3 and 4 on the server. Key point: the server never sees data or extractor weights, only prototype vectors, and what it sends back is a tiny linear classifier that acts as a teacher.");
}

// =====================================================================
// 5. Methodology: losses
// =====================================================================
{
  const s = content("Proposed Methodology", "PROPOSED METHODOLOGY · OBJECTIVES", "Three Learning Signals", "PROPOSED METHODOLOGY");
  const cards = [
    ["A", "Irrelevant-class KD (client)", "L_local = L_CE + T² · KL( p̂ᵗ ‖ p̂ˢ ),  p̂ = softmax over classes j ≠ y", "Teacher = the client's own best model from earlier rounds. The target class is removed before the softmax, so the KD gradient on it is exactly zero; it only preserves how the client relates the other classes (protects against forgetting)."],
    ["B", "Global decision boundary learner (server)", "L_g = − Σ_c y_c · log g(p)_c ,   p ∈ Pᵍ = P¹ ∪ … ∪ P^M", "g has exactly the structure of a client head. Trained on the multi-prototypes of all clients, it sees every client's class regions, which no single client can."],
    ["C", "Global boundary distillation (client)", "L_col = (1−α)·L_CE + α·T²·KL( σ(g(z)/T) ‖ σ(h(z)/T) ),  z = f(x)", "g is applied to the client's own features z, so the local head h learns the global boundary without forcing heterogeneous feature spaces to align."],
  ];
  cards.forEach(([k, t, eq, d], i) => {
    const y = 1.25 + i * 1.22;
    card(s, 0.5, y, 9.0, 1.1);
    num(s, k, 0.68, y + 0.16, 0.34, i === 1 ? TEAL : NAVY);
    txt(s, t, { x: 1.15, y: y + 0.12, w: 3.4, h: 0.3, fontSize: 13, bold: true, color: NAVY });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.15, y: y + 0.48, w: 3.6, h: 0.48, rectRadius: 0.04, fill: { color: WHITE }, line: { color: BORDER, width: 0.75 } });
    txt(s, eq, { x: 1.25, y: y + 0.48, w: 3.45, h: 0.48, fontFace: "Cambria", fontSize: 10, italic: true, color: NAVY, valign: "middle" });
    txt(s, d, { x: 5.0, y: y + 0.12, w: 4.35, h: 0.9, fontSize: 10.5, color: SLATE, valign: "middle" });
  });
  txt(s, [{ text: "Paper defaults (all kept): ", options: { bold: true, color: NAVY } }, { text: "v = 5 · α = 0.7 · T = 20 · 100 k-means iterations · 5 local, 5 update and 5 server epochs per round" }], { x: 0.5, y: 4.95, w: 9.0, h: 0.25, fontSize: 10.5, color: SLATE });
  s.addNotes("A is the local objective: cross-entropy plus non-target-class distillation from the best previous version of the same client. B is the server objective: plain cross-entropy over the union of all prototypes. C is the collaborative objective: the local head is pulled towards g's softened predictions on the client's own features. We kept every hyperparameter at the paper's value.");
}

// =====================================================================
// 6. Implementation: architecture
// =====================================================================
pres.addSection({ title: "Implementation" });
{
  const s = content("Implementation", "IMPLEMENTATION · CODE STRUCTURE", "Built on HtFLlib, Fed-GDBD Written from Scratch", "IMPLEMENTATION");
  txt(s, "Repository layout", { x: 0.5, y: 1.25, w: 4.3, h: 0.28, fontSize: 12, bold: true, color: NAVY });
  code(s, [
    "FedGDBD-repro/",
    "├─ dataset/generate_Cifar10.py  Dir(0.1) split",
    "├─ system/main.py          + FedGDBD + args",
    "├─ system/flcore/clients/",
    "│   ├─ clientgdbd.py       NEW · 195 lines",
    "│   ├─ clientproto.py      FedProto",
    "│   └─ clientlg.py         LG-FedAvg",
    "├─ system/flcore/servers/",
    "│   └─ servergdbd.py       NEW · 102 lines",
    "├─ setup.bat · run_cifar10/100.bat",
    "└─ check_progress.bat · progress.py",
  ], 0.5, 1.58, 4.4, 2.75, 10.5);
  txt(s, "Server loop (servergdbd.py)", { x: 5.1, y: 1.25, w: 4.4, h: 0.28, fontSize: 12, bold: true, color: NAVY });
  code(s, [
    "for c in clients: c.pretrain()",
    "init_global_learner()        # Eq. 5",
    "for r in range(R + 1):",
    "    evaluate()       # + teacher pick",
    "    for c in clients:",
    "        c.train()    # Eq. 11 + k-means++",
    "    train_global_learner()   # Eq. 12",
    "    for c in clients:",
    "        c.update()   # Eq. 13",
  ], 5.1, 1.58, 4.4, 2.75, 10.5);
  const notes = [
    ["Base library", "HtFLlib (KDD'25 benchmark): same models, Dirichlet split and baselines as the paper"],
    ["Our additions", "Fed-GDBD client + server, CLI flags, PyTorch ≥ 2.6 load fix, Windows launch and progress scripts"],
  ];
  notes.forEach(([h, d], i) => {
    const x = 0.5 + i * 4.6;
    txt(s, [{ text: h + ": ", options: { bold: true, color: TEAL } }, { text: d }], { x, y: 4.5, w: 4.4, h: 0.6, fontSize: 10.5, color: SLATE });
  });
  s.addNotes("We built on HtFLlib because its heterogeneous-model setup matches the paper exactly: same four models, same Dirichlet partitioning, same FedProto and LG-FedAvg implementations. That makes the baseline comparison fair. Fed-GDBD itself is about 300 lines we wrote: a client class and a server class. The server loop on the right is the whole algorithm.");
}

// =====================================================================
// 7. Implementation: key code
// =====================================================================
{
  const s = content("Implementation", "IMPLEMENTATION · KEY CODE", "Losses and Clustering in Code", "IMPLEMENTATION");
  txt(s, "Irrelevant-class KD  (clientgdbd.py)", { x: 0.5, y: 1.22, w: 5.4, h: 0.26, fontSize: 11.5, bold: true, color: NAVY });
  code(s, [
    "def ikd_loss(s, t, y):   # student / teacher logits",
    "    m = one_hot(y).bool()          # hide target class",
    "    s = s.masked_fill(m, -1e4) / T",
    "    t = t.masked_fill(m, -1e4) / T",
    "    return KL(softmax(t) ‖ softmax(s))",
  ], 0.5, 1.5, 5.4, 1.25, 9.5);
  txt(s, "Boundary distillation step  (update)", { x: 0.5, y: 2.92, w: 5.4, h: 0.26, fontSize: 11.5, bold: true, color: NAVY });
  code(s, [
    "rep = model.base(x);  out = model.head(rep)",
    "with no_grad(): g_out = g(rep)   # global teacher",
    "loss = (1-α)*CE(out, y) + α*T²*KL(g_out ‖ out)",
    "loss.backward(); optimizer.step()",
  ], 0.5, 3.2, 5.4, 1.05, 9.5);
  txt(s, "k-means++ prototypes", { x: 6.15, y: 1.22, w: 3.35, h: 0.26, fontSize: 11.5, bold: true, color: NAVY });
  code(s, [
    "C = seed_kmeanspp(z, v)",
    "  # P(z) ∝ d(z)²",
    "for _ in range(100):",
    "  a = cdist(z,C).argmin(1)",
    "  oh = one_hot(a)",
    "  C' = ohᵀz / oh.sum(0)",
    "  if C' == C: break",
    "  C = C'",
  ], 6.15, 1.5, 3.35, 2.75, 9.5);
  const pts = [
    "Teacher logits come from the best past local model (picked by test accuracy at each evaluation)",
    "g is frozen during distillation; gradients reach only the local extractor and head",
    "Bug found and fixed: masking the target AFTER the softmax pushed the correct logit down and made CIFAR-100 diverge (NaN at round 8)",
  ];
  txt(s, pts.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < pts.length - 1 } })), { x: 0.5, y: 4.4, w: 9.0, h: 0.75, fontSize: 10.5, color: SLATE, paraSpaceAfter: 2 });
  s.addNotes("Three pieces of code carry the method. The IKD loss is ordinary KL with the target-class column masked out. The update step is two lines: run g on the client's own features without gradient, then mix cross-entropy with the distillation term. Clustering is k-means++ seeding followed by vectorised Lloyd iterations, capped at 100 like the paper.");
}

// =====================================================================
// 8. Experimental setup & reproduction scope
// =====================================================================
{
  const s = content("Implementation", "IMPLEMENTATION · EXPERIMENTAL SETUP", "Reproduction Scope: Paper vs Ours", "IMPLEMENTATION");
  const H = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.navy } } });
  const rows = [
    [H("Aspect"), H("Paper"), H("Our reproduction")],
    ["Methods compared", "5: Fed-GDBD, FedProto, FedTGP, LG-FedAvg, FedGH", "3: Fed-GDBD, FedProto, LG-FedAvg  (+ our FedGDBD-S)"],
    ["Datasets", "4: CIFAR-10, CIFAR-100, Tiny-ImageNet, Flowers102", "2: CIFAR-10, CIFAR-100"],
    ["Heterogeneity settings", "Practical Dir(0.1) + pathological", "Practical Dir(0.1) only"],
    ["Variants / ablations", "Main + ablations, v/T/α sweeps, 8-model test", "Main variant only"],
    ["Global rounds × repeats", "100 rounds × 3 runs", "50 rounds × 1 run (faithful Fed-GDBD stopped at round 9–10)"],
    ["Hardware", "1 × RTX 3080 server, 128 GB RAM", "RTX 3050 6 GB (CIFAR-10) + RTX 5060 8 GB (CIFAR-100) laptops, 3 runs in parallel per GPU"],
    ["Kept identical", "20 clients · 4 models · batch 10 · lr 0.01 · E = 5 · v = 5 · α = 0.7 · T = 20", "same"],
  ];
  s.addTable(rows, {
    x: 0.5, y: 1.25, w: 9.0, colW: [1.9, 3.45, 3.65], rowH: 0.36,
    fontFace: "Calibri", fontSize: 10.5, color: "22262E", valign: "middle",
    border: { type: "solid", pt: 0.5, color: HEX.border }, margin: [0.04, 0.08, 0.04, 0.08],
  });
  card(s, 0.5, 4.5, 9.0, 0.6, TINT_T, TINT_T);
  txt(s, [{ text: "Why reduced: ", options: { bold: true, color: NAVY } }, { text: "the full paper is ≈ 1,500+ GPU-hours; our budget was ≈ 15 hours on two laptops. We kept the paper's headline experiment (Table 1, practical setting) and every hyperparameter." }], { x: 0.7, y: 4.5, w: 8.6, h: 0.6, fontSize: 11, valign: "middle" });
  s.addNotes("Be upfront about scope. We compare 3 of the 5 methods, 2 of the 4 datasets, one heterogeneity setting, the main variant only, 50 instead of 100 rounds and one run instead of three. Everything that defines the method, clients, models and hyperparameters, is identical to the paper. The reduction was forced by compute: about 1,500 GPU-hours for the full paper versus about 15 hours on two laptops.");
}

// =====================================================================
// 9. Results table
// =====================================================================
const R10 = JSON.parse(require("fs").readFileSync("../analysis/summary_cifar10.json", "utf8"));
const R100 = JSON.parse(require("fs").readFileSync("../analysis/summary_cifar100.json", "utf8"));
pres.addSection({ title: "Results Analysis" });
{
  const s = content("Results Analysis", "RESULTS ANALYSIS · ACCURACY", "Test Accuracy: Ours vs Paper (Practical, β = 0.1)", "RESULTS ANALYSIS");
  const H = (t, fill = HEX.navy) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: fill }, align: "center" } });
  const SH = (t) => ({ text: t, options: { bold: true, color: HEX.navy, fill: { color: "E7EAF3" }, align: "center" } });
  const N = (t, o = {}) => ({ text: t, options: Object.assign({ align: "center", color: "22262E" }, o) });
  const D = (t) => ({ text: t, options: { align: "center", color: t.startsWith("+") ? HEX.teal : HEX.slate, bold: true } });
  const rows = [
    [H("Method"), { text: "CIFAR-10", options: { colspan: 3, bold: true, color: "FFFFFF", fill: { color: HEX.navy }, align: "center" } }, { text: "CIFAR-100", options: { colspan: 3, bold: true, color: "FFFFFF", fill: { color: HEX.navy }, align: "center" } }],
    [SH(""), SH("Ours"), SH("Paper"), SH("Δ"), SH("Ours"), SH("Paper"), SH("Δ")],
    [N("FedProto", { align: "left", bold: true }), N("82.52"), N("82.75", { color: HEX.slate }), D("−0.23"), N("39.51"), N("35.38", { color: HEX.slate }), D("+4.13")],
    [N("LG-FedAvg", { align: "left", bold: true }), N("86.36"), N("86.64", { color: HEX.slate }), D("−0.28"), N("42.79"), N("43.30", { color: HEX.slate }), D("−0.51")],
    [N("Fed-GDBD, faithful *", { align: "left", bold: true }), N("85.70"), N("87.90", { color: HEX.slate }), D("−2.20"), N("40.70"), N("45.09", { color: HEX.slate }), D("−4.39")],
    [{ text: "FedGDBD-S (ours)", options: { align: "left", bold: true, color: "FFFFFF", fill: { color: HEX.teal } } }, N("87.10", { bold: true, fill: { color: "DFEDF0" } }), N("87.90", { color: HEX.slate, fill: { color: "DFEDF0" } }), { text: "−0.80", options: { align: "center", bold: true, color: HEX.slate, fill: { color: "DFEDF0" } } }, N("43.74", { bold: true, fill: { color: "DFEDF0" } }), N("45.09", { color: HEX.slate, fill: { color: "DFEDF0" } }), { text: "−1.35", options: { align: "center", bold: true, color: HEX.slate, fill: { color: "DFEDF0" } } }],
  ];
  s.addTable(rows, {
    x: 0.5, y: 1.22, w: 9.0, colW: [2.1, 1.15, 1.15, 1.15, 1.15, 1.15, 1.15], rowH: 0.34,
    fontFace: "Calibri", fontSize: 11.5, color: "22262E", valign: "middle",
    border: { type: "solid", pt: 0.5, color: HEX.border },
  });
  const tiles = [
    ["FedGDBD-S vs best baseline", "+0.74 / +0.95", "points over LG-FedAvg (CIFAR-10 / CIFAR-100)"],
    ["Gap to paper's Fed-GDBD", "−0.80 / −1.35", "points, with 50 instead of 100 rounds and 1 seed"],
    ["Baselines reproduced", "≤ 0.5 pt", "from the paper, except FedProto on CIFAR-100 (+4.1)"],
  ];
  tiles.forEach(([h, v, d], i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 3.42, 2.85, 1.1);
    txt(s, h, { x: x + 0.18, y: 3.5, w: 2.55, h: 0.26, fontSize: 10.5, bold: true, color: NAVY });
    txt(s, v, { x: x + 0.18, y: 3.76, w: 2.55, h: 0.38, fontFace: "Cambria", fontSize: 18, bold: true, color: TEAL, valign: "middle" });
    txt(s, d, { x: x + 0.18, y: 4.14, w: 2.55, h: 0.34, fontSize: 9.5, color: SLATE });
  });
  txt(s, "Metric: average of the 20 clients' local test accuracies, best round of 50 (paper protocol). * Faithful Eq. 13: best round before the collapse (round 1 / round 2); stopped after 9–10 rounds.", { x: 0.5, y: 4.65, w: 9.0, h: 0.45, fontSize: 10, italic: true, color: SLATE });
  s.addNotes("Main table. Both baselines land within half a point of the paper, except FedProto on CIFAR-100, which we beat by four points. The faithful Fed-GDBD peaks early and then collapses, so its best number is 2 to 4 points below the paper. Our stabilised FedGDBD-S is the best method we ran on both datasets: plus 0.74 and plus 0.95 over LG-FedAvg, and 0.8 and 1.35 points below the paper's Fed-GDBD, with half the rounds and one seed.");
}

// =====================================================================
// 10. Convergence
// =====================================================================
{
  const s = content("Results Analysis", "RESULTS ANALYSIS · CONVERGENCE", "Accuracy over 50 Communication Rounds", "RESULTS ANALYSIS");
  const labels = Array.from({ length: 51 }, (_, i) => String(i));
  const pad = (a) => labels.map((_, i) => (i < a.length ? Math.round(a[i] * 100) / 100 : null));
  const mk = (R, ds) => [
    { name: "FedProto", labels, values: pad(R[`${ds}_FedProto`].acc) },
    { name: "LG-FedAvg", labels, values: pad(R[`${ds}_LG-FedAvg`].acc) },
    { name: "Fed-GDBD (faithful)", labels, values: pad(R[`${ds}_FedGDBD`].acc) },
    { name: "FedGDBD-S (ours)", labels, values: pad(R[`${ds}_FedGDBD-S`].acc) },
  ];
  const opts = (x, title, min, max) => ({
    x, y: 1.15, w: 4.45, h: 2.75,
    chartColors: [HEX.muted, HEX.navy, "C0504D", HEX.teal], lineSize: 2, lineDataSymbol: "none",
    showTitle: true, title, titleFontSize: 11, titleColor: HEX.navy, titleFontFace: "+mn-lt",
    catAxisLabelColor: HEX.slate, catAxisLabelFontSize: 9, catAxisLabelFontFace: "+mn-lt", catAxisLabelFrequency: 10, catAxisLabelRotate: 0,
    valAxisLabelColor: HEX.slate, valAxisLabelFontSize: 9, valAxisLabelFontFace: "+mn-lt", valAxisMinVal: min, valAxisMaxVal: max,
    valGridLine: { color: HEX.border, size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 9, legendColor: HEX.slate, legendFontFace: "+mn-lt",
    displayBlanksAs: "gap",
  });
  s.addChart(pres.charts.LINE, mk(R10, "Cifar10"), opts(0.5, "CIFAR-10: test accuracy (%) vs round", 50, 90));
  s.addChart(pres.charts.LINE, mk(R100, "Cifar100"), opts(5.05, "CIFAR-100: test accuracy (%) vs round", 0, 50));
  const obs = [
    ["Stability", "Faithful Fed-GDBD peaks at round 1–2, then falls to 75.5 % / 28.0 %. FedGDBD-S stays within ±0.5 pt of its best for all 50 rounds."],
    ["Speed", "Both Fed-GDBD variants reach within 1 pt of their best by round 2–5; baselines need 13–31 rounds (helped by 5 pre-training epochs)."],
    ["Cost", "FedGDBD-S ≈ 10 min/round vs 5–10 for baselines: two local passes plus clustering every round."],
  ];
  obs.forEach(([h, d], i) => {
    const x = 0.5 + i * 3.05;
    num(s, i + 1, x, 4.08, 0.28, i === 0 ? TEAL : NAVY);
    txt(s, [{ text: h + ": ", options: { bold: true, color: NAVY } }, { text: d }], { x: x + 0.36, y: 4.04, w: 2.6, h: 1.05, fontSize: 9.5, color: SLATE });
  });
  s.addNotes("Two things to point at. First, the red line: the faithful Fed-GDBD is the best method for the first couple of rounds and then degrades steadily, which is why we stopped it. Second, the teal line: with our stabilisation it keeps the early lead and stays flat for all 50 rounds. Fed-GDBD converges much faster than the baselines, partly because it starts from five epochs of local pre-training.");
}

// =====================================================================
// 11. Novelty: FedGDBD-S
// =====================================================================
pres.addSection({ title: "Novelty" });
{
  const s = content("Novelty", "NOVELTY · OUR CONTRIBUTION", "FedGDBD-S: Stabilising Global Boundary Distillation", "NOVELTY");
  const P = (ds, algo) => (ds === "c10" ? R10 : R100)[`${ds === "c10" ? "Cifar10" : "Cifar100"}_${algo}`].per;
  const last = (a) => a[a.length - 1].map((v) => Math.round(v * 10) / 10);
  const archs = ["CNN", "GoogLeNet", "MobileNetV2", "ResNet18"];
  s.addChart(pres.charts.BAR, [
    { name: "Fed-GDBD faithful (round 10)", labels: archs, values: last(P("c100", "FedGDBD")) },
    { name: "FedGDBD-S (round 50)", labels: archs, values: last(P("c100", "FedGDBD-S")) },
  ], {
    x: 0.5, y: 1.15, w: 4.4, h: 2.85, barDir: "col", barGrouping: "clustered",
    chartColors: ["C0504D", HEX.teal],
    showTitle: true, title: "CIFAR-100 accuracy (%) by client architecture", titleFontSize: 10.5, titleColor: HEX.navy, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 9, dataLabelColor: HEX.slate, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: HEX.slate, catAxisLabelFontSize: 9, catAxisLabelFontFace: "+mn-lt",
    valAxisLabelColor: HEX.slate, valAxisLabelFontSize: 9, valAxisLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 60,
    valGridLine: { color: HEX.border, size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 9, legendColor: HEX.slate, legendFontFace: "+mn-lt",
  });
  const items = [
    ["Diagnosis", "One linear g serves four feature spaces; on some, its logits dwarf the head's and α·T² = 280 swamps CE. CNN 48 → 4 % (CIFAR-100), ResNet18 79 → 53 % (CIFAR-10)."],
    ["Fix 1: logit-scale matching", "g̃(z) = g(z) · std(h(z)) / std(g(z)), per sample, so the teacher's confidence matches the student's scale."],
    ["Fix 2: head-only distillation", "The KD term updates only the head h(stop-grad(z)); cross-entropy still trains the full model, so g cannot distort the extractor."],
  ];
  items.forEach(([h, d], i) => {
    const y = 1.15 + i * 0.98;
    card(s, 5.1, y, 4.4, 0.88, i ? TINT : TINT_T, i ? BORDER : TINT_T);
    num(s, i === 0 ? "!" : i, 5.25, y + 0.12, 0.3, i ? NAVY : TEAL);
    txt(s, h, { x: 5.65, y: y + 0.1, w: 3.7, h: 0.28, fontSize: 11.5, bold: true, color: NAVY, valign: "middle" });
    txt(s, d, { x: 5.65, y: y + 0.38, w: 3.75, h: 0.48, fontSize: 9, color: SLATE });
  });
  card(s, 0.5, 4.2, 9.0, 0.9, NAVY, NAVY);
  txt(s, [
    { text: "Result: ", options: { bold: true, color: WHITE } },
    { text: "87.10 % / 43.74 %, the best of all methods we ran, with zero extra communication and a two-line code change.", options: { color: WHITE, breakLine: true } },
    { text: "Next ideas (not yet tested): per-class prototype count v_c ∝ feature variance; per-client α_i from local–global prototype alignment.", options: { color: ICE, fontSize: 9.5 } },
  ], { x: 0.7, y: 4.2, w: 8.6, h: 0.9, fontSize: 11, valign: "middle" });
  s.addNotes("This is our novelty, and it came from the reproduction itself. Per-client logs showed the faithful method only fails on particular architectures: the CNN clients on CIFAR-100 and the ResNet18 clients on CIFAR-10. Our explanation: g is one linear layer for four different feature spaces, and the large distillation weight lets it override local learning. Two changes fix it: rescale g's logits to the student's scale, and let the distillation term train only the head. The chart shows the CNN clients going from 4 percent back to 46 percent. The adaptive v and alpha ideas from our proposal remain future work.");
}

// =====================================================================
// 12. Conclusion
// =====================================================================
pres.addSection({ title: "Conclusion" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Conclusion" });
  txt(s, "CONCLUSION", { x: 0.6, y: 0.4, w: 8, h: 0.25, fontSize: 9, bold: true, color: ICE, charSpacing: 1 });
  txt(s, "What We Learned", { x: 0.6, y: 0.68, w: 8.8, h: 0.55, fontFace: "Cambria", fontSize: 26, bold: true, color: WHITE, valign: "middle" });
  const pts = [
    ["Reproduced", "Fed-GDBD re-implemented from the paper alone. Both baselines match the paper within 0.5 pt (FedProto on CIFAR-100 is 4.1 pt better)."],
    ["Finding", "Taken literally, Eq. 13 is unstable: whole architectures collapse after round 2. We also found and fixed one IKD masking bug of our own."],
    ["Result", "FedGDBD-S: 87.10 % (CIFAR-10) and 43.74 % (CIFAR-100), best of all methods we ran; +0.7 / +1.0 pt over LG-FedAvg, 0.8 / 1.35 pt below the paper."],
    ["Limits and next", "1 seed, 50 rounds, 2 datasets, practical split only. Next: 3 seeds, pathological split, adaptive v_c / α_i, Tiny-ImageNet."],
  ];
  pts.forEach(([h, d], i) => {
    const x = 0.6 + (i % 2) * 4.45, y = 1.5 + Math.floor(i / 2) * 1.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.25, h: 1.4, rectRadius: 0.06, fill: { color: "2C3B63" }, line: { color: "2C3B63" } });
    num(s, i + 1, x + 0.18, y + 0.18, 0.32, TEAL);
    txt(s, h, { x: x + 0.62, y: y + 0.18, w: 3.4, h: 0.32, fontSize: 13, bold: true, color: WHITE, valign: "middle" });
    txt(s, d, { x: x + 0.2, y: y + 0.6, w: 3.9, h: 0.75, fontSize: 10.5, color: ICE });
  });
  txt(s, "Thank you  ·  Questions?", { x: 0.6, y: 4.75, w: 8.8, h: 0.4, fontFace: "Cambria", fontSize: 16, bold: true, color: WHITE });
  s.addNotes("Four takeaways: we reproduced the setup and the baselines closely; implementing the paper's equations literally exposed an instability; our two-line stabilisation makes Fed-GDBD the best method in our runs; and the main limitation is one seed and fifty rounds.");
}


(async () => {
  await pres.writeFile({ fileName: "Fed-GDBD_Final_Presentation.pptx" });
  await applyTheme("Fed-GDBD_Final_Presentation.pptx", THEME);
  console.log("done");
})();
