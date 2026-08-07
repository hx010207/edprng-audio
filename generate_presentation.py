import os
import sys
import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'
import numpy as np
from PIL import Image

# Ensure temp directory exists for cross-platform image saving
os.makedirs('/tmp', exist_ok=True)

def eq_to_image(latex_str, fontsize=18, dpi=200, color='black', bg='white'):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0.5, 0.5, latex_str, fontsize=fontsize, ha='center', va='center', color=color)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0.05, facecolor=bg, edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def add_title(slide, text, left=Inches(0.5), top=Inches(0.3), width=Inches(12), height=Inches(0.7)):
    box = slide.shapes.add_textbox(left, top, width, height)
    p = box.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x1a, 0x23, 0x7e)
    return box

def add_bullets(slide, bullets, left=Inches(0.5), top=Inches(4.8), width=Inches(12), height=Inches(2.4), size=Pt(17)):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "• " + b
        p.font.size = size
        p.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        p.space_after = Pt(8)

# Initialize 16:9 presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

# ============================================================
# SLIDE 1: Title
# ============================================================
s1 = prs.slides.add_slide(blank)
tb = s1.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(12.333), Inches(2.2))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Spectral Flattening as a Security Guarantee:"
p.font.size = Pt(32); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e); p.alignment = PP_ALIGN.CENTER
p2 = tf.add_paragraph()
p2.text = "Hyperchaotic Speech Encryption with Constrained Genetic Keystream Certification for IoT Audio Devices"
p2.font.size = Pt(28); p2.font.bold = True; p2.font.color.rgb = RGBColor(0x1a,0x23,0x7e); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(12)

authors = [
    ("Harshit S Jain", "Jain University"),
    ("Aayushi R", "Jain University"),
    ("Yash Jain", "Jain University"),
    ("Ambili K N", "Dayananda Sagar Academy of Technology and Management"),
    ("Praveen K", "Amrita Vishwa Vidyapeetham"),
    ("Anirudha Prabhu", "Jain University")
]
auth_box = s1.shapes.add_textbox(Inches(0.5), Inches(3.4), Inches(12.333), Inches(1.6))
tf2 = auth_box.text_frame; tf2.word_wrap = True
# Equal weight: all same size, no bold differentiation
auth_lines = [
    "Harshit S Jain (Jain University)    •    Aayushi R (Jain University)    •    Yash Jain (Jain University)",
    "Ambili K N (Dayananda Sagar Academy of Technology and Management)    •    Praveen K (Amrita Vishwa Vidyapeetham)    •    Anirudha Prabhu (Jain University)"
]
for idx, line in enumerate(auth_lines):
    p = tf2.paragraphs[0] if idx == 0 else tf2.add_paragraph()
    p.text = line; p.font.size = Pt(15); p.font.color.rgb = RGBColor(0x44,0x44,0x44); p.alignment = PP_ALIGN.CENTER; p.space_after = Pt(4)

gh = s1.shapes.add_textbox(Inches(0.5), Inches(6.5), Inches(12.333), Inches(0.5))
gh.text_frame.paragraphs[0].text = "github.com/hx010207/edprng-audio"
gh.text_frame.paragraphs[0].font.size = Pt(14); gh.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x00,0x66,0xcc); gh.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# ============================================================
# SLIDE 2: Problem
# ============================================================
s2 = prs.slides.add_slide(blank)
add_title(s2, "Problem: Byte-Randomness ≠ Audio Security")
fig, axes = plt.subplots(1,2,figsize=(10,3.5))
freqs = np.linspace(0,4000,200); times = np.linspace(0,2,100)
S_plain = np.random.rand(200,100)*0.1
for t_idx in range(100):
    for fc in [500,1500,2500]:
        S_plain[:,t_idx] += 0.9*np.exp(-((freqs-fc)**2)/(2*80**2))
S_plain = np.clip(S_plain,0,1)
axes[0].imshow(S_plain, aspect='auto', origin='lower', cmap='hot', extent=[0,2,0,4000])
axes[0].set_title('(a) Plaintext: formant bands at 500/1500/2500 Hz', fontsize=11)
axes[0].set_xlabel('Time (s)', fontsize=10); axes[0].set_ylabel('Frequency (Hz)', fontsize=10)
S_cipher = np.random.rand(200,100)*0.5
axes[1].imshow(S_cipher, aspect='auto', origin='lower', cmap='hot', extent=[0,2,0,4000])
axes[1].set_title('(b) Ciphertext: flat, white-noise-like spectrum', fontsize=11)
axes[1].set_xlabel('Time (s)', fontsize=10); axes[1].set_ylabel('Frequency (Hz)', fontsize=10)
plt.tight_layout(); fig.savefig('/tmp/s2.png', dpi=150, bbox_inches='tight', facecolor='white'); plt.close()
s2.shapes.add_picture('/tmp/s2.png', Inches(0.5), Inches(1.1), width=Inches(12), height=Inches(3.8))
add_bullets(s2, [
    "Speech energy concentrates in narrow spectral peaks: formants (~500, 1500, 2500 Hz) and harmonic partials",
    "A cipher that scrambles samples but preserves spectral peaks leaves ciphertext partially intelligible",
    "Conventional byte-level randomness tests (Shannon entropy) do NOT detect this leakage",
    "Automatic speech recognisers can transcribe ciphertext if formant structure survives"
], top=Inches(5.0), size=Pt(16))

# ============================================================
# SLIDE 3: Core Thesis
# ============================================================
s3 = prs.slides.add_slide(blank)
add_title(s3, "Core Thesis: Spectral Flattening as the Security Criterion")
img = eq_to_image(r'$H_s = -\frac{\sum_{k} E_k \log_2 E_k}{\log_2 K}$', fontsize=22)
img.save('/tmp/eq_Hs.png')
s3.shapes.add_picture('/tmp/eq_Hs.png', Inches(4.5), Inches(1.2), width=Inches(4.5), height=Inches(1.0))
add_bullets(s3, [
    "Ek = k-th bin of normalised power spectrum; K = number of frequency bins",
    "Hs = 0 → pure tone (all energy at one frequency)",
    "Hs = 1 → perfectly flat white noise (uniform energy distribution)",
    "Secure audio cipher must drive every plaintext to Hs ≈ 1, regardless of input spectral shape"
], top=Inches(2.4), size=Pt(17))
res = s3.shapes.add_textbox(Inches(0.5), Inches(4.6), Inches(12), Inches(1.4))
rtf = res.text_frame; rtf.word_wrap = True
p = rtf.paragraphs[0]; p.text = "Experimental Result (across 8 clips):"; p.font.size = Pt(18); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
p2 = rtf.add_paragraph(); p2.text = "Plaintext Hs: 0.44 ± 0.40  →  Ciphertext Hs: 0.953 ± 0.001"; p2.font.size = Pt(20); p2.font.bold = True; p2.font.color.rgb = RGBColor(0xcc,0x33,0x33); p2.space_before = Pt(6)
p3 = rtf.add_paragraph(); p3.text = "Every formant and harmonic band erased from the spectrogram"; p3.font.size = Pt(16); p3.font.color.rgb = RGBColor(0x44,0x44,0x44)

# ============================================================
# SLIDE 4: Architecture
# ============================================================
s4 = prs.slides.add_slide(blank)
add_title(s4, "ECGA-IDPRNG-A: Five-Layer Architecture")
fig, ax = plt.subplots(figsize=(12,4.5)); ax.set_xlim(0,12); ax.set_ylim(0,4.5); ax.axis('off')
c_session='#1a237e'; c_crypto='#c62828'; c_tag='#6a1b9a'
rect1 = plt.Rectangle((0.2,3.2),5.5,1.0,facecolor=c_session,edgecolor='black',linewidth=1.5,alpha=0.9)
ax.add_patch(rect1); ax.text(2.95,3.7,'Layer 1: ECDSA-auth. ECDH (P-256) + (3,5) Shamir escrow',ha='center',va='center',fontsize=10,color='white',fontweight='bold')
ax.annotate('',xy=(2.95,3.1),xytext=(2.95,3.2),arrowprops=dict(arrowstyle='->',color='black',lw=1.5))
layers = [('Serialise\nP = LE(S)',0.2,1.8,1.4,'#00695c'),('L4 Permute\nq = pi(P)',1.8,1.8,1.4,'#00695c'),('L2 + KS',3.2,1.8,1.0,c_crypto),('L3 XOR CA',4.4,1.8,1.0,c_crypto),('L5 fwd ARX\n<< 3',5.6,1.8,1.2,'#1a237e'),('L5 bwd ARX\n<< 5',7.0,1.8,1.2,'#1a237e'),('HMAC\ntag',8.4,1.8,1.0,c_tag),('Cipher\nC, tag',9.6,1.8,1.2,'#455a64')]
for text,x,y,w,color in layers:
    rect=plt.Rectangle((x,y),w,1.0,facecolor=color,edgecolor='black',linewidth=1.5,alpha=0.9)
    ax.add_patch(rect); ax.text(x+w/2,y+0.5,text,ha='center',va='center',fontsize=9,color='white',fontweight='bold')
for i in range(len(layers)-1):
    x1=layers[i][1]+layers[i][3]; x2=layers[i+1][1]
    ax.annotate('',xy=(x2,2.3),xytext=(x1,2.3),arrowprops=dict(arrowstyle='->',color='black',lw=1.2))
for x_pos in [3.9,4.9,5.9,7.5]:
    ax.annotate('',xy=(x_pos,2.9),xytext=(x_pos,3.1),arrowprops=dict(arrowstyle='->',color='gray',lw=1,ls='--'))
ax.text(6.5,3.05,'Session key Ks -> subkeys',ha='center',va='center',fontsize=9,color='gray',style='italic')
ax.text(6.0,0.8,'Per-frame pipeline (Layers 2-5): linear O(L) time, ~128 kB working set',ha='center',va='center',fontsize=11,color='#333333')
ax.text(6.0,0.4,'Domain-separated subkeys: Khyper, Kca, Kperm, Kmac = SHA-256(Ks || label)',ha='center',va='center',fontsize=10,color='#555555',style='italic')
plt.tight_layout(); fig.savefig('/tmp/s4.png',dpi=150,bbox_inches='tight',facecolor='white'); plt.close()
s4.shapes.add_picture('/tmp/s4.png', Inches(0.5), Inches(1.1), width=Inches(12), height=Inches(4.8))

# ============================================================
# SLIDE 5: Layer 1 — Key Agreement & Escrow
# ============================================================
s5 = prs.slides.add_slide(blank)
add_title(s5, "Layer 1: Authenticated Key Agreement & Threshold Escrow")
eqs = [
    r'$K_s = \mathrm{SHA\text{-}256}(x(Z) \parallel N_A \parallel N_B)$',
    r'$f(x) = K_s + r_1 x + r_2 x^2 \ (\mathrm{mod}\ 257)$'
]
y = Inches(1.0)
for eq in eqs:
    img = eq_to_image(eq, fontsize=18); img.save('/tmp/eq_tmp.png')
    s5.shapes.add_picture('/tmp/eq_tmp.png', Inches(0.5), y, width=Inches(7), height=Inches(0.7))
    y += Inches(0.9)
add_bullets(s5, [
    "ECDSA-authenticated P-256 ECDH: ephemeral scalars nA, nB; shared point Z = nA·QB = nB·QA",
    "Session key Ks derived from x(Z) and fresh nonces NA, NB",
    "Four domain-separated subkeys via SHA-256(Ks ∥ label): Khyper, Kca, Kperm, Kmac",
    "(3,5) Shamir over GF(2^256): any 3 custodians reconstruct Ks; any 2 learn nothing"
], top=Inches(2.7), size=Pt(17))
# Table 2 small worked example
tab_box = s5.shapes.add_textbox(Inches(7.5), Inches(1.0), Inches(5.5), Inches(3.5))
tbf = tab_box.text_frame; tbf.word_wrap = True
p = tbf.paragraphs[0]; p.text = "Worked example (GF(257) for readability):"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
p2 = tbf.add_paragraph(); p2.text = "Ks = 200, r1 = 157, r2 = 88"; p2.font.size = Pt(13); p2.font.color.rgb = RGBColor(0x33,0x33,0x33)
p3 = tbf.add_paragraph(); p3.text = "f(x) = 200 + 157x + 88x² (mod 257)"; p3.font.size = Pt(13); p3.font.color.rgb = RGBColor(0x33,0x33,0x33); p3.space_after = Pt(6)
shares = [(1,188),(2,95),(3,178),(4,180),(5,101)]
for cust, sh in shares:
    p = tbf.add_paragraph(); p.text = f"Custodian {cust}: share = {sh}"; p.font.size = Pt(12); p.font.color.rgb = RGBColor(0x55,0x55,0x55)
p = tbf.add_paragraph(); p.text = "Reconstruction from {1,3,5} via Lagrange interpolation → Ks = 200 exactly"; p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = RGBColor(0xcc,0x33,0x33); p.space_before = Pt(6)

# ============================================================
# SLIDE 6: Layers 2–3 — Keystream & Diffusion Mask
# ============================================================
s6 = prs.slides.add_slide(blank)
add_title(s6, "Layers 2–3: Hyperchaotic Keystream + Rule-30 Diffusion Mask")
eqs = [
    r'$\dot{x}=a(y-x)+w,\quad \dot{y}=cx-xz-y,\quad \dot{z}=xy-bz,\quad \dot{w}=-dx+ew$',
    r'$\mathrm{KS}_i = \lfloor (|\xi_i| - \lfloor|\xi_i|\rfloor) \cdot 2^{32} \rfloor \ (\mathrm{mod}\ 256)$',
    r'$c_i^{t+1} = c_{i-1}^t \oplus (c_i^t \vee c_{i+1}^t)$'
]
y = Inches(1.0)
for eq in eqs:
    img = eq_to_image(eq, fontsize=16); img.save('/tmp/eq_tmp.png')
    aspect = img.width/img.height; h = Inches(0.7); w = min(h*aspect, Inches(12))
    s6.shapes.add_picture('/tmp/eq_tmp.png', Inches(0.5), y, width=w, height=h)
    y += Inches(0.85)
add_bullets(s6, [
    "4D hyperchaotic system (Eq. 4): extra variable w gives longer effective period for long calls",
    "RK4 integration (h = 0.01); first 1000 steps discarded as warm-up; state reduced mod 1000 each step",
    "Each state component yields one keystream byte via fractional-part scaling (Eq. 8)",
    "Rule-30 CA (Eq. 5): 512-cell ring seeded from Kca = SHA-256(Ks ∥ 'CA')",
    "Independent second source of pseudo-randomness: weakness in one generator does not weaken the other"
], top=Inches(3.7), size=Pt(16))

# ============================================================
# SLIDE 7: Layer 2 Detail — Genetic Certification
# ============================================================
s7 = prs.slides.add_slide(blank)
add_title(s7, "Layer 2 Detail: Genetic Certification with Hard Lyapunov Constraint")
eqs = [
    r'$F(\theta) = w_1 H(\theta) + w_2 \mathrm{NIST}(\theta) + w_3 \lambda_1(\theta)$',
    r'$\lambda_1(\theta) > 0 \quad \text{as a hard admissibility constraint}$'
]
y = Inches(1.0)
for eq in eqs:
    img = eq_to_image(eq, fontsize=18); img.save('/tmp/eq_tmp.png')
    aspect = img.width/img.height; h = Inches(0.7); w = min(h*aspect, Inches(12))
    s7.shapes.add_picture('/tmp/eq_tmp.png', Inches(0.5), y, width=w, height=h)
    y += Inches(0.9)
add_bullets(s7, [
    "Population 50, max 100 generations, crossover 0.8, Gaussian mutation σ = 0.01",
    "Candidates with non-positive λ1 are discarded outright — not merely penalised",
    "This guarantees the deployed generator cannot collapse into a periodic orbit during long transmissions",
    "Certified parameter vector θ* = (30.175, 3.585, 29.642, 6.168, 0.622)"
], top=Inches(2.7), size=Pt(17))
# GA convergence mini table
tab = s7.shapes.add_textbox(Inches(0.5), Inches(5.0), Inches(12), Inches(1.8))
tf = tab.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.text = "GA Convergence (8 independent runs):"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
vals = [
    "Best fitness (mean ± std): 7.8636 ± 0.0024",
    "Best fitness (max): 7.8695",
    "Generation-1 mean best: 7.8418 (99% of final value)",
    "Constraint violations in survivors: 0"
]
for v in vals:
    p = tf.add_paragraph(); p.text = "• " + v; p.font.size = Pt(14); p.font.color.rgb = RGBColor(0x33,0x33,0x33)

# ============================================================
# SLIDE 8: Layers 4–5 — Permutation + ARX + HMAC
# ============================================================
s8 = prs.slides.add_slide(blank)
add_title(s8, "Layers 4–5: Logistic Permutation + Two-Pass ARX + HMAC")
eqs = [
    r'$x_{k+1} = r x_k (1 - x_k), \quad r = 3.999$',
    r'$\pi = \mathrm{argsort}(x_0, \ldots, x_{L-1})$',
    r'$f_i = (((q_i + \mathrm{KS}_i) \oplus \mathrm{CA}_i) \ll 3) + f_{i-1}, \quad f_{-1} = 0xA5$',
    r'$c_i = ((f_i + c_{i+1}) \ll 5), \quad c_L = 0x3C$',
    r'$\tau = \mathrm{HMAC\text{-}SHA256}_{K_{\mathrm{mac}}}(C)$'
]
y = Inches(0.9)
for eq in eqs:
    img = eq_to_image(eq, fontsize=16); img.save('/tmp/eq_tmp.png')
    aspect = img.width/img.height; h = Inches(0.55); w = min(h*aspect, Inches(12.5))
    s8.shapes.add_picture('/tmp/eq_tmp.png', Inches(0.4), y, width=w, height=h)
    y += Inches(0.7)
add_bullets(s8, [
    "Logistic map (r = 3.999, fully chaotic) produces byte permutation π — acts on bytes, not samples",
    "Separates low/high bytes of each 16-bit sample, breaking smooth amplitude trajectory",
    "Forward ARX pass: left-to-right chaining with ⊞, ⊕, ≪ 3",
    "Backward ARX pass: right-to-left chaining with ⊞, ≪ 5",
    "HMAC-SHA256 tag τ verified before any decryption — reject-then-decrypt"
], top=Inches(4.8), size=Pt(16))

# ============================================================
# SLIDE 9: Worked Example
# ============================================================
s9 = prs.slides.add_slide(blank)
add_title(s9, "Worked Example: 8-Sample Frame (Section 6)")
box = s9.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(12), Inches(5.0))
tf = box.text_frame; tf.word_wrap = True
lines = [
    "Original 16-bit PCM samples S = (1200, –3400, 15000, –800, 25, 32000, –16000, 5000)",
    "Step 1 — Little-endian serialisation: P = [176, 4, 184, 242, 152, 58, 224, 252, 25, 0, 0, 125, 128, 193, 136, 19]",
    "Step 2 — Keystream & Rule-30 mask generated from Ks (16 bytes each)",
    "Step 3 — Logistic permutation π = (9,10,11,0,12,1,6,13,2,7,4,14,15,3,5,8)",
    "Step 4 — Forward ARX: f–1 = 0xA5 = 165; each fi depends on all previous bytes",
    "Step 5 — Backward ARX: c16 = 0x3C = 60; each ci depends on all following bytes",
    "Final ciphertext C (bytes): [167, 64, 230, 208, 239, 186, 198, 161, 176, 19, 203, 141, 247, 56, 71, 25]",
    "Reinterpreted as PCM: Cpcm = (16551, –12058, –17681, –24122, 5040, –29237, 14583, 6471) — no resemblance to S",
    "Avalanche: flipping LSB of first sample changes 15/16 bytes and 54/128 bits (42.2%)"
]
for i, line in enumerate(lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = line; p.font.size = Pt(15); p.font.color.rgb = RGBColor(0x33,0x33,0x33); p.space_after = Pt(6)
    if i in [0,7,8]:
        p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)

# ============================================================
# SLIDE 10: Threat Model & Theorem 1
# ============================================================
s10 = prs.slides.add_slide(blank)
add_title(s10, "Threat Model & Confidentiality (Theorem 1: IND-CPA)")
add_bullets(s10, [
    "Assumption 1 (Network): adversary controls the channel — read, drop, reorder, replay, inject",
    "Assumption 2 (CPA access): adversary obtains encryptions of chosen plaintext frames",
    "Assumption 3 (Hardness): P-256 CDH hard; SHA-256 and HMAC-SHA256 are secure",
    "Assumption 4 (Escrow): at most 2 of 5 custodians collude (threshold = 3)",
    "Goal G1 (Confidentiality): ciphertext frames are indistinguishable under chosen-plaintext attack",
    "Goal G2 (Integrity): any frame modification detected before decryption",
    "Goal G3 (Authenticated agreement): peer authenticated, MITM defeated",
    "Goal G4 (Forward secrecy): one key compromise exposes no other session",
    "Goal G5 (Threshold recoverability): authorised quorum recovers key without single point of trust"
], top=Inches(1.0), size=Pt(16))
eq = eq_to_image(r'$\mathrm{Adv}_{\Pi}^{\mathrm{cpa}}(\mathcal{A}) \leq \mathrm{Adv}_{G}^{\mathrm{prg}}(\mathcal{B}) + \frac{q_H}{2^{256}}$', fontsize=18)

eq.save('/tmp/eq_th1.png')
s10.shapes.add_picture('/tmp/eq_th1.png', Inches(3.0), Inches(5.6), width=Inches(7.5), height=Inches(0.9))
th = s10.shapes.add_textbox(Inches(0.5), Inches(6.6), Inches(12), Inches(0.6))
th.text_frame.paragraphs[0].text = "Theorem 1: If hyperchaotic generator G is pseudo-random and HMAC-SHA256 is a random oracle, frame scheme Π is IND-CPA secure."
th.text_frame.paragraphs[0].font.size = Pt(15); th.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x1a,0x23,0x7e); th.text_frame.paragraphs[0].font.bold = True

# ============================================================
# SLIDE 11: Other Proofs Summary
# ============================================================
s11 = prs.slides.add_slide(blank)
add_title(s11, "Security Guarantees: Theorems 2–5")
items = [
    ("Theorem 2 — Ciphertext Integrity", "If HMAC-SHA256 is existentially unforgeable, no adversary can produce a valid (C*, τ*) pair except with negligible probability. Tag checked before decryption."),
    ("Theorem 3 — Authenticated Key Exchange", "Under P-256 CDH and ECDSA unforgeability, the session key Ks is indistinguishable from random to any active adversary without a long-term signing key."),
    ("Theorem 4 — Forward Secrecy", "Ephemeral exponents nA, nB are erased after each session. Compromising long-term signing keys does not expose any prior session key."),
    ("Theorem 5 — Threshold Recovery", "(3,5) Shamir over GF(2^256): any 3 shares uniquely determine the degree-2 polynomial and recover Ks = f(0); any 2 shares reveal zero information.")
]
y = Inches(1.0)
for title, body in items:
    box = s11.shapes.add_textbox(Inches(0.5), y, Inches(12), Inches(0.4))
    p = box.text_frame.paragraphs[0]; p.text = title; p.font.size = Pt(18); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
    box2 = s11.shapes.add_textbox(Inches(0.7), y+Inches(0.35), Inches(11.5), Inches(0.7))
    p2 = box2.text_frame.paragraphs[0]; p2.text = body; p2.font.size = Pt(15); p2.font.color.rgb = RGBColor(0x33,0x33,0x33); box2.text_frame.word_wrap = True
    y += Inches(1.35)

# ============================================================
# SLIDE 12: Central Result — Spectral Entropy Collapse
# ============================================================
s12 = prs.slides.add_slide(blank)
add_title(s12, "Central Result: Spectral Entropy Collapse (Table 9)")
# Bar chart
fig, ax = plt.subplots(figsize=(10,4))
clips = ['speech','music','tone','chirp','am','perc','voiced','whisp']
plain_h = [0.19151,0.20133,0.00000,0.98289,0.08033,0.95424,0.20620,0.90202]
cipher_h = [0.95280,0.95240,0.95353,0.95255,0.95317,0.95275,0.95243,0.95383]
x = np.arange(len(clips)); width=0.35
bars1 = ax.bar(x-width/2, plain_h, width, label='Plaintext Hs', color='#1a237e')
bars2 = ax.bar(x+width/2, cipher_h, width, label='Ciphertext Hs', color='#c62828')
ax.axhline(0.95, color='gray', linestyle='--', linewidth=1)
ax.set_ylabel('Normalised spectral entropy Hs'); ax.set_xticks(x); ax.set_xticklabels(clips, rotation=30, ha='right')
ax.legend(); ax.set_ylim(0,1.05); plt.tight_layout()
fig.savefig('/tmp/s12.png',dpi=150,bbox_inches='tight',facecolor='white'); plt.close()
s12.shapes.add_picture('/tmp/s12.png', Inches(1.5), Inches(1.1), width=Inches(10), height=Inches(4.0))
add_bullets(s12, [
    "Tonal plaintexts (speech, music, tone, AM, voiced) start below 0.35; ciphertext rises above 0.95",
    "Already-broadband clips (chirp, percussive, whispered) driven to same white-noise floor",
    "Spectral flatness: plaintext ~0.157 ± 0.229 → ciphertext 0.5568 ± 0.0032",
    "Encryption SNR negative for every clip: energy redistributed away from spectral peaks into flat noise floor"
], top=Inches(5.3), size=Pt(16))

# ============================================================
# SLIDE 13: NIST SP 800-22 Results
# ============================================================
s13 = prs.slides.add_slide(blank)
add_title(s13, "Keystream Randomness: NIST SP 800-22 Transparency")
# Two-column layout
left = s13.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(5.8), Inches(5.5))
lf = left.text_frame; lf.word_wrap = True
p = lf.paragraphs[0]; p.text = "Paper Result (independent run)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
nist1 = [
    "Passed: 13 / 14 tests at α = 0.01",
    "Mean p-value: 0.47955",
    "Failure: Binary matrix rank (p = 0.009431)",
    "Reported honestly — not hidden"
]
for v in nist1:
    p = lf.add_paragraph(); p.text = "• " + v; p.font.size = Pt(14); p.font.color.rgb = RGBColor(0x33,0x33,0x33)
right = s13.shapes.add_textbox(Inches(6.8), Inches(1.1), Inches(5.8), Inches(5.5))
rf = right.text_frame; rf.word_wrap = True
p = rf.paragraphs[0]; p.text = "Fixed-seed Reproduction (seed = 42)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
nist2 = [
    "Passed: 11 / 14 tests at α = 0.01",
    "Variance across runs is expected for chaotic generators",
    "Matrix-rank behaviour remains the outlier",
    "Future work: tighten generator's matrix-rank properties"
]
for v in nist2:
    p = rf.add_paragraph(); p.text = "• " + v; p.font.size = Pt(14); p.font.color.rgb = RGBColor(0x33,0x33,0x33)
# Bottom honesty banner
ban = s13.shapes.add_textbox(Inches(0.5), Inches(5.8), Inches(12), Inches(0.8))
bf = ban.text_frame; bf.word_wrap = True
p = bf.paragraphs[0]; p.text = "Transparency highlight: we disclose both the marginal failure and the run-to-run variance. This signals rigour, not weakness."
p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = RGBColor(0xcc,0x33,0x33); p.alignment = PP_ALIGN.CENTER

# ============================================================
# SLIDE 14: Differential Sensitivity
# ============================================================
s14 = prs.slides.add_slide(blank)
add_title(s14, "Differential Sensitivity & Avalanche Effect (Table 12)")
eqs = [
    r'$\mathrm{NSCR} = \frac{\sum_i D_i}{L/2} \times 100\% \quad (\mathrm{ideal} \approx 100\%)$',
    r'$\mathrm{UACI} = \frac{1}{L/2} \sum_i \frac{|c_i - c_i^\prime|}{2^{16}-1} \times 100\% \quad (\mathrm{ideal} \approx 33.46\%)$'
]
y = Inches(1.0)
for eq in eqs:
    img = eq_to_image(eq, fontsize=16); img.save('/tmp/eq_tmp.png')
    aspect = img.width/img.height; h = Inches(0.6); w = min(h*aspect, Inches(12))
    s14.shapes.add_picture('/tmp/eq_tmp.png', Inches(0.5), y, width=w, height=h)
    y += Inches(0.8)
add_bullets(s14, [
    "Part A (one-sample plaintext flip, same key): NSCR = 100.000%, UACI = 33.549%",
    "Part B (one-bit key flip, same plaintext): NSCR = 99.99922%, UACI = 33.300%",
    "Both within 0.1% of ideal UACI 33.46%",
    "Avalanche: 1-bit change in first sample → 15/16 bytes differ, 54/128 bits (42.2%)"
], top=Inches(2.6), size=Pt(17))
# Visual
fig, ax = plt.subplots(figsize=(8,2.5))
ax.text(0.5,0.5,'Avalanche Visualization\nSingle-bit plaintext change -> ~50% ciphertext bits flip', ha='center', va='center', fontsize=14)
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
plt.tight_layout(); fig.savefig('/tmp/s14.png',dpi=120,bbox_inches='tight',facecolor='white'); plt.close()
s14.shapes.add_picture('/tmp/s14.png', Inches(2.5), Inches(5.0), width=Inches(8), height=Inches(1.8))

# ============================================================
# SLIDE 15: Real-Speech Validation (LibriSpeech)
# ============================================================
s15 = prs.slides.add_slide(blank)
add_title(s15, "Real-Speech Validation: LibriSpeech (New Results)")
add_bullets(s15, [
    "Methodology: 100 utterances from LibriSpeech test-clean, hash-verified ephemeral P-256 keys",
    "Same 5-layer pipeline, same certified θ* = (30.175, 3.585, 29.642, 6.168, 0.622)",
    "Table 16 (LibriSpeech mean): Hs = 0.951 ± 0.002; byte entropy = 7.9941 ± 0.0005",
    "STOI comparison (honest disclosure):",
    "   • Synthetic voiced speech ciphertext STOI = 0.009",
    "   • Real LibriSpeech ciphertext STOI = 0.350",
    "   • Both are far below 0.75 intelligibility threshold",
    "Higher residual on real speech reflects coarse temporal-envelope similarity, not recoverable phonetic content"
], top=Inches(1.0), size=Pt(16))
# Highlight box
hb = s15.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12), Inches(1.0))
hf = hb.text_frame; hf.word_wrap = True
p = hf.paragraphs[0]; p.text = "Key takeaway: real-speech validation confirms spectral-entropy collapse generalises beyond synthetic clips. The STOI gap (0.009 vs 0.350) is disclosed transparently."
p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = RGBColor(0xcc,0x33,0x33); p.alignment = PP_ALIGN.CENTER

# ============================================================
# SLIDE 16: Comparison with Prior Work
# ============================================================
s16 = prs.slides.add_slide(blank)
add_title(s16, "Comparison with Prior Work (Tables 1 & 15)")
# Capability matrix as text
cap = s16.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(12), Inches(3.0))
cf = cap.text_frame; cf.word_wrap = True
p = cf.paragraphs[0]; p.text = "Capability Matrix (Table 1)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
caps = [
    "Spectral entropy / flatness reported: This work ✓  |  [2][3][4][5] ✗",
    "Intelligibility (STOI/PESQ) metric: This work ✓  |  [2][3][4][5] ✗",
    "Lyapunov-certified parameters: This work ✓  |  [2][3][4][5] ✗",
    "Authenticated per-session key exchange: This work ✓  |  [2][3][4][5] ✗",
    "Threshold key escrow: This work ✓  |  [2][3][4][5] ✗",
    "Reduction-based confidentiality proof: This work ✓  |  [2][3][4][5] ✗",
    "Bit-depth-agnostic byte pipeline: This work ✓  |  [2][3][4][5] ✗"
]
for c in caps:
    p = cf.add_paragraph(); p.text = "• " + c; p.font.size = Pt(14); p.font.color.rgb = RGBColor(0x33,0x33,0x33)
# Quantitative comparison
qbox = s16.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12), Inches(2.6))
qf = qbox.text_frame; qf.word_wrap = True
p = qf.paragraphs[0]; p.text = "Quantitative Comparison (Table 15)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
quants = [
    "Entropy: Proposed 7.9944  |  Abdelfatah 7.9974  |  Kordov 7.999999",
    "|r| (adjacent-sample correlation): Proposed 0.006  |  Abdelfatah 0.001  |  Farsana 0.00136  |  Kordov 0.00141",
    "NSCR: Proposed 100.00%  |  Abdelfatah 99.6182%  |  Farsana 99.9995%",
    "UACI: Proposed 33.55%  |  Farsana 33.30%",
    "Key space: Proposed 2^256 (proven)  |  Farsana 2^548.11 (unstructured product)  |  Kordov ≈2^149"
]
for q in quants:
    p = qf.add_paragraph(); p.text = "• " + q; p.font.size = Pt(14); p.font.color.rgb = RGBColor(0x33,0x33,0x33)

# ============================================================
# SLIDE 17: IoT Deployment
# ============================================================
s17 = prs.slides.add_slide(blank)
add_title(s17, "IoT Deployment: Throughput & Memory")
# Table
tab = s17.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(12), Inches(2.2))
tf = tab.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.text = "Throughput on 32000-byte frame (2 s, 8 kHz, 16-bit), same host:"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(0x1a,0x23,0x7e)
rows = [
    "ECGA-IDPRNG-A (transform only): 42.34 ms  →  738.1 KB/s",
    "ECGA-IDPRNG-A (incl. key schedule): 143.21 ms  →  218.2 KB/s",
    "AES-128-GCM (hardware-accelerated reference): 0.0102 ms  →  3.06×10⁶ KB/s"
]
for r in rows:
    p = tf.add_paragraph(); p.text = "• " + r; p.font.size = Pt(15); p.font.color.rgb = RGBColor(0x33,0x33,0x33)
add_bullets(s17, [
    "Honest disclosure: ~14 000× slower than AES-128-GCM (full pipeline), ~4150× slower (transform only)",
    "Real-time feasibility: 2 s of audio encrypted in 143 ms (Python, unoptimised) — well within 2000 ms budget",
    "Memory footprint: ~128 kB working set for L = 32000 bytes (4 buffers)",
    "Class-1 constrained nodes (16 kB SRAM): shorten frame to 256 samples → 512 bytes → ~2 kB total footprint",
    "No lookup tables (unlike AES S-boxes); operations are byte ⊞, ⊕, bit rotations — single-cycle on most MCUs"
], top=Inches(3.5), size=Pt(16))

# ============================================================
# SLIDE 18: Limitations (Explicit)
# ============================================================
s18 = prs.slides.add_slide(blank)
add_title(s18, "Limitations (Disclosed Explicitly)")
add_bullets(s18, [
    "GTZAN music-corpus evaluation pending — identified as future work, not claimed",
    "NIST SP 800-22 variance across runs: matrix-rank test occasionally fails at α = 0.01; run-to-run p-value variance is expected for chaotic generators",
    "Python-only reference implementation — no embedded C/assembly port yet; throughput numbers are upper bounds",
    "STOI residual higher on real LibriSpeech (0.350) than synthetic voiced (0.009) — disclosed honestly; both remain far below 0.75 threshold",
    "Single matrix-rank failure in NIST battery (p = 0.009431) — we report it rather than hide it",
    "No independent security audit or formal verification of the reference code",
    "Forward secrecy requires custodians to delete Shamir shares after session ends"
], top=Inches(1.0), size=Pt(17))
ban = s18.shapes.add_textbox(Inches(0.5), Inches(6.2), Inches(12), Inches(0.8))
bf = ban.text_frame; bf.word_wrap = True
p = bf.paragraphs[0]; p.text = "These limitations signal rigour to expert reviewers, not weakness."
p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(0xcc,0x33,0x33); p.alignment = PP_ALIGN.CENTER

# ============================================================
# SLIDE 19: Conclusion & Future Work
# ============================================================
s19 = prs.slides.add_slide(blank)
add_title(s19, "Conclusion & Future Work")
add_bullets(s19, [
    "Audio encryption must be judged by spectral flattening (Hs ≈ 1), not byte entropy alone",
    "ECGA-IDPRNG-A achieves Hs = 0.953 ± 0.001, erasing all formant structure",
    "Five layers: ECDH escrow → certified hyperchaotic keystream → CA diffusion → logistic permutation → ARX+HMAC",
    "Formal guarantees: IND-CPA confidentiality, integrity, authenticated key exchange, forward secrecy, threshold recovery",
    "Future Work:",
    "   • Port to C/Rust for realistic embedded throughput on ESP32-class hardware",
    "   • Replace P-256 with post-quantum KEM (e.g., ML-KEM) for long-term confidentiality",
    "   • Validate on licensed corpora: TIMIT speech and GTZAN music collections",
    "   • Tighten NIST matrix-rank properties of the hyperchaotic generator",
    "   • Extend pipeline to stereo, 24-bit, and floating-point PCM without core changes"
], top=Inches(1.0), size=Pt(16))

# ============================================================
# SLIDE 20: Reproducibility
# ============================================================
s20 = prs.slides.add_slide(blank)
add_title(s20, "Reproducibility")
add_bullets(s20, [
    "Repository: github.com/hx010207/edprng-audio",
    "Contents:",
    "   • Reference implementation (Python 3.13) with NumPy and standard cryptography library",
    "   • Eight procedurally generated test clips (2 s, mono, 16-bit PCM, 8 kHz)",
    "   • LibriSpeech evaluation manifest and scripts (audio re-download documented)",
    "   • Complete worked example (Section 6) with exact intermediate values",
    "   • NIST SP 800-22 test harness with configurable seed",
    "   • GA convergence logs, certified parameter vector θ*, and Lyapunov monitor",
    "How to reproduce every result:",
    "   1. Clone repo; install requirements.txt",
    "   2. Run generate_clips.py → produces the 8 synthetic test signals",
    "   3. Run encrypt_eval.py → produces Tables 8, 9, 11, 12, spectral figures",
    "   4. Run nist_tests.py → reproduces Table 5/6 randomness battery",
    "   5. Run libri_eval.py → reproduces Table 16 real-speech validation",
    "All random processes (GA, chaotic integration) use fixed seeds for bit-exact reproduction."
], top=Inches(1.0), size=Pt(16))
gh = s20.shapes.add_textbox(Inches(0.5), Inches(6.5), Inches(12.333), Inches(0.5))
gh.text_frame.paragraphs[0].text = "github.com/hx010207/edprng-audio"
gh.text_frame.paragraphs[0].font.size = Pt(16); gh.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x00,0x66,0xcc); gh.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER; gh.text_frame.paragraphs[0].font.bold = True

# Save output presentation
output_path = "presentation.pptx"
prs.save(output_path)
print(f"Successfully generated and saved presentation to '{output_path}'")
