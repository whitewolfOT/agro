---
name: hakim-medicine-catalog
description: >
  Provides a historically faithful catalog of classical hakim (Unani/Greco-Islamic)
  medicine remedies. Use when the user asks for "hakim remedies", "traditional medicine
  treatments", "herbal formulas", "Unani medicine", or detailed historical prescriptions.
  Includes herbs, spices, roots, animal parts, minerals, venoms, oils, distillates,
  and compound formulas.
---

# Hakim Medicine Catalog Skill

## Overview

This skill enables Claude to produce a complete, historically accurate catalog of classical
hakim (حکیم) remedies rooted in the Unani (Greco-Islamic) medical tradition, as practiced
across Persia, the Arab world, the Indian subcontinent, and North Africa from roughly the
9th through the 19th centuries CE.

---

## Source Hierarchy & Translation Policy

### Tier 1 — Arabic Text (Primary Base) ✅ Always preferred

The Arabic text is the most accurate reflection of Avicenna's intent and must be used
as the primary base for all entries.

- **Ibn Sina (Avicenna)** — *القانون في الطب* (*Al-Qanun fi al-Tibb*, Canon of Medicine)
  → Use modern critical Arabic editions: **Bulaq edition** (Cairo, 1877) or
    **Cairo critical edition** for reliability. These are the standard scholarly baseline.
- **Ibn Rushd (Averroes)** — *كتاب الكليات* (*Kitab al-Kulliyyat*)
- **Al-Biruni** — *كتاب الصيدنة* (*Kitab al-Saydana*)
- **Al-Zahrawi (Abulcasis)** — *التصريف* (*Al-Tasrif*)
- **Dioscorides** — Arabic translation (*De Materia Medica*)
- **Hakim Muhammad Sharif Khan** — *Ilaj al-Amraz* (إلاج الأمراض)
- **Hakim Ajmal Khan** — classical compound formularies

**Naming rule from Arabic**: When presenting ingredient or formula names, always lead
with the Arabic or original name (e.g., *صفصاف* safṣāf, *حبة السوداء* ḥabbatus sawdā').
Transliterate faithfully. Do not substitute a Latinized corruption as the primary name.

### Tier 2 — Modern Annotated English Translation ✅ Recommended companion

Use alongside the Arabic to preserve meaning while ensuring readability:

- **Laleh Bakhtiar** — *The Canon of Medicine* (Great Books of the Islamic World, 1999)
  → Preferred modern English annotated translation; use for sense-checking and explanation.
- Other peer-reviewed academic translations where available.

Translate passages into clear English yourself when needed, using the Arabic as the base.
This preserves meaning that literal Latinized renderings often obscure.

### Tier 3 — Latin Editions (Venice 1595 / 1608) ⚠️ Use with caution

The Latin translations of Avicenna (Gerard of Cremona lineage, printed Venice 1595/1608)
are often "barbarous" — awkward, unintelligible, or so literal in following Arabic syntax
that meaning is distorted or lost.

**Use the Latin only to:**
- Cross-check historical context and see how medieval Europe interpreted a passage
- Resolve genuinely obscure Arabic passages where the Latin may preserve an early reading
- Trace the history of a term's reception in European medicine

**Never use the Latin as the primary source for:**
- Ingredient names (Latin corruptions of Arabic names are frequently unrecognizable)
- Dosage figures (numbers are often garbled in transmission)
- Preparation methods (procedural steps are frequently compressed or mistranslated)

### Barbarous Latin Protocol ⚠️

When a Latin term or passage is barbarous, unintelligible, or misleads the Arabic meaning:

1. **Do not use the Latin term** as the primary name or definition.
2. **Fall back to the Arabic original** or the Persian/Urdu equivalent.
3. **Add ⚠️ CAUTION** prominently in the entry noting that the Latin is unreliable for
   this passage, and that the Arabic text has been used instead.

**Example marker to insert:**

> ⚠️ CAUTION — BARBAROUS LATIN: The Venice edition renders this term in a form that
> does not faithfully reflect the Arabic *[original term]*. The Arabic text and Bulaq
> edition have been used as the authoritative basis for this entry.

### Source Decision Tree

```
Query requires a term, dosage, or procedure from Avicenna
        │
        ▼
Arabic text available? (Bulaq / Cairo edition)
    YES → Use Arabic as base. Transliterate name. ✅
    NO  →
        ▼
Modern annotated English translation available? (Bakhtiar, etc.)
    YES → Use for sense-checking. Cross-reference. ✅
    NO  →
        ▼
Latin edition only available?
        │
        ├─ Latin is clear and consistent with Arabic context?
        │       YES → Use Latin for historical context only;
        │             note "cross-checked with Venice edition"
        │
        └─ Latin is barbarous / unintelligible / contradicts Arabic?
                YES → Discard Latin reading.
                      Use Arabic/original name.
                      Add ⚠️ CAUTION — BARBAROUS LATIN marker.
```

---

## Classical Source Library

| Source | Language | Edition / Version | Role |
|--------|----------|-------------------|------|
| *Al-Qanun fi al-Tibb* — Ibn Sina | Arabic | Bulaq 1877; Cairo critical ed. | **Primary base** |
| *The Canon of Medicine* — Bakhtiar trans. | English | Great Books of the Islamic World, 1999 | Annotated companion |
| *Kitab al-Kulliyyat* — Ibn Rushd | Arabic | — | Secondary Arabic source |
| *Kitab al-Saydana* — Al-Biruni | Arabic | — | Materia medica reference |
| *Al-Tasrif* — Al-Zahrawi | Arabic | — | Surgical & compound formulas |
| *De Materia Medica* — Dioscorides | Arabic trans. | — | Greek-Arabic bridge source |
| *Canon Medicinae* — Venice ed. | Latin | 1595 / 1608 | Historical cross-check only ⚠️ |

---

## Step 1: Identify Category

Determine the ailment, symptom, or bodily system the user wants treatment for.
Recognized categories:

| Code | Category |
|------|----------|
| DIG | Digestive remedies |
| FEV | Fever remedies |
| RES | Respiratory remedies |
| WND | Wound care & external injuries |
| JNT | Joint, muscle & nerve pain |
| HUM | Blood & humoral balancing |
| LIV | Liver & spleen remedies |
| WOM | Women's health |
| CHI | Children's ailments |
| SKN | Skin diseases |
| EYE | Eye treatments |
| HRT | Heart-strengthening remedies |
| CLM | Calming / sleep remedies |
| LAX | Laxatives |
| PUR | Purgatives |
| DIU | Diuretics |
| TON | General tonics & restoratives |
| APH | Aphrodisiacs & reproductive tonics |
| EXT | External applications (liniments, poultices, oils) |
| SUR | Surgical preparations |
| TOX | Toxic & antidotal therapies |

If the user's query is ambiguous, ask which category or symptom they mean before proceeding.

---

## Step 2: Retrieve Remedies

For the requested category:

1. **List every classical ingredient or compound formula** relevant to it.
2. **Specify all preparation methods** historically used:
   - *Oral forms*: decoction (جوشاندہ), infusion, powder (سفوف), electuary (معجون),
     pill (حب), syrup (شربت), confection (قرص), distillate (عرق), troche (قرص)
   - *Topical forms*: paste, poultice (ضماد), liniment (روغن), suppository, pessary,
     plaster (لیپ), ointment (مرہم), kohl (for eyes)
   - *Other forms*: fumigation (دھونی), steam inhalation, enema (حقنہ), bath, wash
3. **Note method of administration**: oral, topical, inhalation, rectal, ophthalmic, etc.
4. **State the traditional use** per classical hakim doctrine.
5. **Include classical dosage & timing** where recorded.
6. **Note temperament** (mizaj) of the remedy — Hot/Cold, Moist/Dry in degrees 1–4.
7. **Note any combination rules**, seasonal or age considerations, contraindications,
   and cautions (including toxicity warnings for dangerous substances).

---

## Step 3: Output Structure

Present results as a structured Markdown table:

```
| Category | Ingredient / Formula | Arabic / Urdu Name | Temperament | Preparation | Administration | Traditional Use | Classical Notes & Cautions |
```

Example row:

| Category | Ingredient / Formula | Arabic / Urdu Name | Temperament | Preparation | Administration | Traditional Use | Classical Notes & Cautions |
|----------|---------------------|--------------------|-------------|-------------|---------------|-----------------|---------------------------|
| FEV | Willow bark | صفصاف | Cold 2°, Dry 1° | Decoction: 5 g bark in 200 ml water, simmer 10 min | Oral | Reduces harārat (heat), restores humoral balance | 3× daily; avoid in weak constitution or cold temperament; combine with honey to offset dryness |

---

## Step 4: Reference Files

- For extended herb monographs → load `references/herbs.md`
- For compound formula details → load `references/formulas.md`
- For output templates (reports, patient cards) → load `assets/templates/`

Load reference files only when the user requests deeper information or when a remedy
requires qualification from classical sources.

---

## Step 5: Troubleshooting

| Problem | Action |
|---------|--------|
| Query is too broad | Ask for specific symptom or category |
| Ingredient has multiple classical names | List all synonyms; lead with Arabic, then Persian/Urdu, then Latin if reliable |
| Latin term is barbarous or unintelligible | Discard Latin; use Arabic or original name; add ⚠️ CAUTION — BARBAROUS LATIN |
| Latin contradicts Arabic text | Arabic text takes precedence; note discrepancy with ⚠️ CAUTION |
| Remedy involves toxic substance | Add prominent ⚠️ CAUTION row |
| Compound formula has many ingredients | Reference `references/formulas.md` for full breakdown |
| Preparation method is unclear | Provide step-by-step instructions in the notes column |
| Unsure which edition of Arabic text to use | Default to Bulaq 1877 or Cairo critical edition; note edition used |

---

## Step 6: Guiding Principles

- **Arabic first**: The Arabic text (Bulaq / Cairo editions) is the authoritative base.
  Never privilege a Latin reading over the Arabic original.
- **Laleh Bakhtiar as companion**: Use the modern annotated English translation alongside
  the Arabic to verify sense and preserve meaning in output.
- **Latin for context only**: The Venice 1595/1608 Latin editions are useful for tracing
  medieval European reception, not for primary definitions, dosages, or procedures.
- **Barbarous Latin → Arabic fallback + ⚠️ CAUTION**: When a Latin term is unintelligible
  or distorts the Arabic, discard it, use the Arabic or original name, and flag prominently.
- **Historical fidelity first**: Do not modernize, sanitize, or reinterpret classical remedies.
  If a hakim text prescribed it, catalog it faithfully.
- **All material classes are valid**: herbs, spices, roots, resins, gums, seeds, barks,
  minerals (mercury, sulfur, arsenic compounds), metals (gold, silver leaf), animal parts
  (bile, horn, fat), venoms (scorpion, snake — classically detoxified), oils, and distillates.
- **Toxic therapies**: Catalog with full classical preparation and detoxification protocols.
  Always flag with ⚠️ CAUTION. This is historical documentation, not modern prescription.
- **Humoral framework**: Always note temperament (mizaj) and humoral action (bile, phlegm,
  blood, black bile) where classically described.
- **Progressive disclosure**: Load `references/herbs.md` and `references/formulas.md`
  only when extended detail is needed — do not load by default.
- **No simplification**: Do not omit ingredients or steps because they seem unusual
  by modern standards.
