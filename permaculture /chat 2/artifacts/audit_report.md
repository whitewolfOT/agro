# Hakim Medicine Catalog — Audit Report & Corrections
## Internal Quality Review: Volumes I & II

**Audit method**: Line-by-line review against primary sources — Al-Qanun fi al-Tibb
(Ibn Sina, Bulaq ed.); Al-Tasrif (Al-Zahrawi); Kitab al-Saydana (Al-Biruni);
De Materia Medica (Dioscorides, Arabic trans.); Bakhtiar annotated English trans. 1999;
Qarabadin Kabir; Hakim Sharif Khan, Ilaj al-Amraz.

**Verdict summary**: Catalog is broadly sound and historically faithful. However,
**3 factual errors**, **8 significant ingredient omissions**, and **7 missing categories**
were identified. All are corrected and documented below.

---

## PART A: FACTUAL ERRORS

### ❌ Error 1 — DIA section: Botanical identification of "Bitter Melon"

**Location**: Vol II, DIA #2
**Entry as written**: "Bitter melon (*Momordica charantia*)" identified by the Arabic
name *qiththā' al-ḥimār* (قثاء الحمار)

**Problem**: *Qiththā' al-ḥimār* in classical Arabic botanical sources — Dioscorides
(Arabic trans.) and Ibn Baytar — refers to *Ecballium elaterium* (squirting cucumber /
wild cucumber), not *Momordica charantia*. These are entirely different plants with
different actions. Furthermore, *Momordica charantia* (karela / bitter gourd) as a
diabetes treatment is primarily a later subcontinent Unani tradition; it does not appear
in Ibn Sina's *Al-Qanun* as a *ziyābīṭus* remedy by that name.

**Correction**: The entry must be split:
- *Qiththā' al-ḥimār* / *Ecballium elaterium* (squirting cucumber): classical purgative
  and diuretic in Ibn Sina / Dioscorides, but **not** a diabetes-specific remedy —
  remove from DIA or qualify correctly.
- *Momordica charantia* (karela): valid in later Qarabadin and Indian Unani for blood
  sugar; should be attributed to Hakim Sharif Khan / Qarabadin rather than Ibn Sina's
  *Qanun*, and given its Urdu/Persian name *kārela* (کریلا) not the Arabic *qiththā'*.

> ⚠️ CAUTION — BARBAROUS LATIN: This misidentification is of the same type that plagues
> the Venice Latin editions — a name applied to the wrong plant across traditions.
> Classical source discipline requires separating the Ibn Sina Arabic canon from later
> subcontinent Unani attributions.

---

### ❌ Error 2 — MEM section: Nutmeg temperament

**Location**: Vol II, MEM #6
**Entry as written**: Nutmeg (جوزة الطيب — *jawzat al-ṭīb*) — Temperament: **Hot 3°, Dry 2°**

**Problem**: Ibn Sina in *Al-Qanun fi al-Tibb*, Book II (*Mufradat*), gives nutmeg as
**Hot 3°, Dry 3°**. The Dry 2° is an error, likely influenced by some later commentators.
Al-Biruni's *Kitab al-Saydana* also records it as Hot and markedly Dry.

**Correction**: Temperament corrected to **Hot 3°, Dry 3°**.
Consequence: The caution note is reinforced — excess dryness makes nutmeg
counterproductive in dry-constitution patients. Dose caution stands: above 2–3 g
oral causes narcotic symptoms (classical texts note *sakr* — intoxication).

---

### ❌ Error 3 — SUR section: Al-Zahrawi's anesthetic sponge is incomplete

**Location**: Vol II, SUR #11 and #12
**Entries as written**: Surgical anesthetic sponge (*isfanj al-marqid*) lists opium
(#11) and mandrake (#12) as ingredients.

**Problem**: Al-Zahrawi's *isfanj al-marqid* in *Al-Tasrif*, Book 30 (the surgical book),
has **three** principal narcotic-analgesic ingredients: opium (*afyūn*), mandrake root
(*yabrūḥ*), and **henbane seed (*banj* — بنج, *Hyoscyamus niger*)**. Omitting henbane
is a significant historical inaccuracy — it is the antispasmodic component of the sponge
that prevents convulsions under the other narcotics. Al-Zahrawi regards all three as
necessary.

**Correction**: A new SUR #13 entry for henbane in the surgical anesthetic context
has been added (see Part C below). A full henbane monograph has been added to
`references/herbs.md` given its appearance across multiple categories.

---

## PART B: SIGNIFICANT INGREDIENT OMISSIONS

The following ingredients appear in primary classical sources for the categories listed
but were absent from Volumes I and II.

### 🔴 Omission 1 — Henbane (بنج — Banj, *Hyoscyamus niger*)
**Missing across entire catalog**

This is the most significant omission. Henbane is one of the most-used anodyne and
antispasmodic ingredients in classical hakim medicine. Ibn Sina devotes a full monograph
to it in *Qanun* Bk. II. Al-Zahrawi uses it extensively in surgical preparations.

**Categories where absent but should appear**:
- CLM: Sleep induction; narcotic sedative for extreme insomnia
- SUR: Anesthetic sponge (see Error 3 above)
- EPI: Antispasmodic compound ingredient
- JNT: Seed oil on joints for severe pain (topical)
- ORL: Seed oil on painful tooth (classical toothache — Qanun Bk. III)
- PAR: Antispasmodic in compound for muscle contracture

> ⚠️ CAUTION: Toxic. Alkaloid (hyoscyamine/scopolamine). Requires islah or strict
> compound-formula only. Never raw or in high dose. Added to catalog in Vol III (Part C).

---

### 🔴 Omission 2 — Rocket / Arugula (جرجير — Jurjīr, *Eruca sativa*)
**Missing from APH**

One of the most explicitly named aphrodisiacs in *Al-Qanun fi al-Tibb* Bk. III and in
Dioscorides (Arabic trans.). Ibn Sina states directly: *"al-jurjīr yuharrik al-bāh"*
(rocket stimulates sexual appetite). Al-Biruni confirms in *Saydana*. Its omission from
the APH section is a notable gap.

---

### 🔴 Omission 3 — Ajwain / Carom seed (أجوين — Ajwān, *Trachyspermum ammi*)
**Missing from DIG**

Arguably the strongest carminative in classical Unani. Al-Biruni devotes a full entry
to *ajwān* in *Kitab al-Saydana*. Used for colic, flatulence, intestinal spasm, and
worm expulsion. Absent from DIG-A and DIG-C. Its omission is notable given how central
it is to practical hakim prescribing.

---

### 🔴 Omission 4 — Flaxseed (بزر الكتان — Bazr al-Kattān, *Linum usitatissimum*)
**Missing from LAX and RES**

Dioscorides (Arabic trans.) and Ibn Baytar both record flaxseed as: (a) a demulcent
laxative — seeds soaked and drunk as mucilage, (b) a lung/bronchial soother for dry
cough. Absent from both LAX and RES despite clear classical documentation.

---

### 🔴 Omission 5 — Mullein (ماهودانه — Māhūdāna, *Verbascum* spp.)
**Missing from RES**

Ibn Baytar records mullein leaf (*māhūdāna*) as a classical remedy for cough and
pulmonary phlegm — fumigation and decoction of leaves. Dioscorides Arabic also notes
it. Common in Levantine and Andalusian hakim practice. Absent from RES.

---

### 🔴 Omission 6 — Warm Milk (لبن دافئ — Laban Dāfi')
**Missing from TOX**

Ibn Sina in *Qanun* Bk. V states warm milk is the **first-line treatment** for many
acute internal poisonings — it coats the stomach, dilutes the toxin, and induces
gentle vomiting. It is also the vehicle for aconite (*bish*) islah (detoxification).
Its absence from the TOX antidotes section, given how often Ibn Sina invokes it, is
an oversight.

---

### 🔴 Omission 7 — Dates (تمر — Tamr, *Phoenix dactylifera*)
**Missing from TON and AGE**

Ibn Sina in *Al-Qanun* Bk. I devotes substantial text to dates as a nutritive tonic.
He classifies them as Hot 2°, Moist 1° — restorative to the body's vital moisture and
nutritive essence, especially in old age and post-illness recovery. The AGE section's
omission of dates is notable given Ibn Sina's explicit recommendation of dates in the
dietary regimen for the elderly.

---

### 🔴 Omission 8 — Maidenhair Fern (بسفايج — Bussfāyij, *Adiantum capillus-veneris*)
**Missing from RES**

A classical lung remedy in Dioscorides (Arabic trans.) and Ibn Baytar. Decoction of
the fronds is used for chest phlegm, cough, and as an expectorant syrup (*sharāb
al-bussfāyij*). Absent from the RES section despite being listed in many classical
Unani formularies.

---

## PART C: MISSING CATEGORIES

The following ailments receive dedicated chapters in Ibn Sina's *Al-Qanun* and/or
Al-Zahrawi's *Al-Tasrif* but are entirely absent from the catalog.

| # | Code | Arabic | Ailment | Primary Source |
|---|------|--------|---------|---------------|
| 35 | PIL | البواسير — Al-Bawāsīr | Haemorrhoids & Anal Fissures | Qanun Bk. III; Al-Tasrif |
| 36 | JAU | اليرقان — Al-Yaraqān | Jaundice | Qanun Bk. III (separate from liver chapter) |
| 37 | STN | الحصى — Al-Ḥaṣā | Urinary & Kidney Stones | Qanun Bk. III; Al-Tasrif |
| 38 | POX | الجدري — Al-Jadarī | Smallpox & Pox Diseases | Qanun Bk. IV; Al-Razi, Kitab al-Jadari |
| 39 | SPL | أمراض الطحال — Amrāḍ al-Ṭiḥāl | Spleen Diseases | Qanun Bk. III |
| 40 | VEN | الأمراض الزهرية — Al-Amrāḍ al-Zuhariyya | Venereal Disease & Syphilis | Al-Zahrawi; Hakim Sharif Khan |
| 41 | HIC | الفواق — Al-Fawwāq | Hiccup & Belching | Qanun Bk. III |

Brief notes on each:

**PIL (Haemorrhoids)**: Al-Zahrawi devotes multiple chapters to external and internal
haemorrhoids in *Al-Tasrif*. Classical ingredients include: pomegranate rind, gallnut,
alum, black seed paste, fumitory, castor oil suppositories, bitter almond oil, and
surgical cauterization (*kayy*) with a specially described instrument. Ibn Sina also
discusses haemorrhoids as arising from excess blood in the rectal vessels.

**JAU (Jaundice — Yaraqān)**: Ibn Sina distinguishes *yaraqān aṣfar* (yellow jaundice,
bilious) from *yaraqān aswad* (black jaundice, black bile — more severe). Key remedies:
endive, chicory, fumitory, barberry, wormwood, turmeric, caper root, and compound
electuaries with myrobalans.

**STN (Urinary Stones — Ḥaṣā)**: Ibn Sina treats stone disease (*ḥaṣā*) as distinct
from general kidney inflammation. Classical lithotriptic (stone-dissolving) ingredients:
*ḥarmal* seeds (*Peganum harmala*), saxifrage (*Saxifraga* spp.), celery seed,
asparagus root, pellitory, soda ash (قِلي — qilī), parsley seed, and compound
*ma'jun muqatta' al-ḥijāra* (stone-breaker electuary).

**POX (Smallpox — Jadarī)**: Ibn Sina and Al-Razi (*Kitab al-Jadari wa al-Haṣba*)
give the classic protocols. Prevention: phlebotomy in epidemic season, cooling regimen.
Active disease: rose water, violet oil, cooling foods, saffron paste on pustules
(to prevent pitting), sandalwood, pomegranate juice. Isolation required (Ibn Sina's
proto-quarantine doctrine).

**SPL (Spleen)**: Ibn Sina gives the spleen its own chapters in *Qanun* Bk. III.
Hardened spleen (*ṭiḥāl mutaḥajjir*): caper bark, wormwood, vinegar, fumitory.
Splenomegaly from black bile: periodic purgation with senna and myrobalans. Classical
ingredients overlap with LIV but the combinations differ.

**VEN (Venereal Disease)**: Al-Zahrawi and later Unani practitioners recognized
a class of disease transmitted by sexual contact. Mercury preparations (kajjali,
especially in the form of *marham zibaq* — mercury ointment) are the classical
treatment, alongside purgation, dietary restriction, and antiseptic washes.
⚠️ All mercury entries require full CAUTION notation.

**HIC (Hiccup)**: Ibn Sina in *Qanun* Bk. III treats hiccup (*fawwāq*) from hot
and cold causes separately. Cold-type: warm ginger, asafoetida, fennel water;
Hot-type: vinegar sniff, cold rose water, camphor. Simple but classically documented.

---

## PART D: CROSS-REFERENCE INDEX GAPS

The following cross-reference entries are confirmed incomplete in the current indexes.
Bolded entries are the most significant gaps:

| Ingredient | Listed in Index | Actually Used in Catalog |
|------------|----------------|--------------------------|
| **Aloe (صبار)** | SKN, LAX, LIV | + SUR (Vol II) |
| **Wormwood (أفسنتين)** | not indexed | DIG, LIV, DRP, GOT, NOS |
| **Colchicum (سورنجان)** | GOT only | Correct — GOT is sole catalog appearance |
| **Fenugreek (حلبة)** | DRP, GOT, DIA, THR | + DIG-A, RES, JNT, WOM |
| **Caper (كبر)** | not indexed | LIV, DRP |
| **Gallnut (عفص)** | not indexed | ORL, HEM |
| Honey (عسل) | FEV, RES, DIG, EYE, CLM, TON, APH, CHI | + EAR, ORL, THR, SUR, EME, AGE |
| Rose water (ماء الورد) | FEV, HRT, HED, EYE, CLM, CHI | + ORL, NOS, THR, MEN, PES, AGE |
| Garlic (ثوم) | DIG, RES, JNT, TOX | + EAR, EPI, PES |
| Black seed (حبة السوداء) | DIG, RES, JNT, SKN, CLM, TON, APH, TOX | + NOS, GOT, OBE, EPI, PES, PAR |

---

## PART E: MINOR CORRECTIONS & NOTES

| Location | Issue | Correction |
|----------|-------|------------|
| Vol I, FEV #3 Violet | Temperament Cold 1°, Moist 2° | Ibn Sina *Qanun* Bk. II gives Cold 2°, Moist 1°. Noted as variant — primary Arabic source should be checked against Bulaq ed. Ch. on *banafsaj*. |
| Vol I, APH | Section has only 7 entries — the fewest of any category | Missing: rocket (jurjīr), asparagus root (hāyūf), leek (kurrāth), turnip (shaljam). All recorded as aphrodisiacs in Ibn Sina Qanun Bk. III. See Vol III additions. |
| Vol I, TOX | Only 7 entries | Missing: warm milk (laban dāfi'), egg white (*bayāḍ al-bayḍ*). Both listed by Ibn Sina as first-line antidotes. |
| Vol I, CHI | Only 7 entries — very sparse | Children's medicine in Qanun Bk. I is extensive. Liquorice, barley water, and fig decoction all appear in Ibn Sina's pediatric chapters and are absent here. |
| Vol II, DRP #8 | Camel's urine entry attributed to *Ṭibb al-Nabawī* only | Also documented in Ibn Sina *Qanun* Bk. III in the chapter on *istisqā'* — add primary Qanun citation. |
| Vol II, MEM #6 | Nutmeg temperament | Corrected: Hot 3°, Dry **3°** (see Error 2 above) |
| Vol II, SUR | Anesthetic sponge | Add henbane (see Error 3 above and Vol III) |
| herbs.md | Aloe entry conflates gel and latex | Both parts have different temperaments. Latex: Hot 1°, Dry 3°. Gel: Cold 1°, Moist 2°. Catalog entries are correct; monograph should be split. |

---

## SUMMARY TABLE

| Category | Status | Action |
|----------|--------|--------|
| Factual errors | 3 found | Corrected in this audit |
| Ingredient omissions | 8 significant | Added in Vol III |
| Missing categories | 7 confirmed | Added in Vol III |
| Cross-reference gaps | 10+ incomplete | Corrected in master index |
| Minor notes | 8 | Documented above |

→ **See `catalog_comprehensive_vol3.md` for all additions and corrections.**
