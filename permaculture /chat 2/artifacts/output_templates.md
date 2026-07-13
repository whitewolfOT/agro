# Hakim Medicine Catalog — Output Templates

Use these templates when generating catalog tables or patient-facing remedy cards.

---

## Template 1: Standard Catalog Table

Copy and fill this table for any remedy category output.

```markdown
| Category | Ingredient / Formula | Arabic / Urdu Name | Temperament | Preparation | Administration | Traditional Use | Classical Notes & Cautions |
|----------|---------------------|--------------------|-------------|-------------|---------------|-----------------|---------------------------|
| [CODE]   | [Name]              | [Arabic/Urdu]      | [Hot/Cold °, Moist/Dry °] | [Method] | [Oral/Topical/etc.] | [Classical indication] | [Dosage, timing, cautions] |
```

---

## Template 2: Single Remedy Detail Card

Use for presenting a single remedy in full detail (e.g., when user asks for a deep-dive).

```markdown
## Remedy: [Name] | [Arabic Name]

**Category**: [Category Code & Name]
**Temperament (Mizaj)**: Hot/Cold °N, Moist/Dry °N
**Primary Indication**: [Main classical use]
**Secondary Indications**: [Additional uses]

### Ingredients
| Ingredient | Qty | Role |
|------------|-----|------|
| ...        | ... | ...  |

### Preparation
1. [Step 1]
2. [Step 2]
...

### Administration
- **Route**: Oral / Topical / Inhalation / Rectal / Ophthalmic
- **Dose**: [Classical dose]
- **Timing**: [Morning / Evening / With meals / On empty stomach]
- **Duration**: [Classical treatment duration if specified]

### Humoral Action
[Describe which humors are targeted: bile, phlegm, blood, black bile]

### Combination Rules
- Combines well with: [ingredients]
- Incompatible with: [ingredients]
- Adjuvants used: [ingredients that modify action]

### Seasonal & Constitutional Notes
- Best temperament for this remedy: [Hot/Cold/Moist/Dry]
- Seasonal preference: [Spring/Summer/Autumn/Winter]
- Age considerations: [Elderly / Children / Adults]

### Classical Source
[Author, Book, Chapter if known]

### Cautions
⚠️ [Any toxicity, contraindications, special preparation requirements]
```

---

## Template 3: Category Summary Header

Use at the top of each category section.

```markdown
## [CATEGORY CODE] — [Category Full Name]

**Humoral Focus**: [Which humor(s) this category primarily addresses]
**Typical Temperament of Remedies**: [General temperament tendency]
**Number of Entries**: [N]
**References**: [herbs.md sections] | [formulas.md sections]

---
[Table follows]
```

---

## Template 4: Toxic Remedy Warning Block

Insert before any table row or section containing known toxic simples.

```markdown
> ⚠️ **CAUTION — TOXIC SUBSTANCE**: The following entry documents a classical remedy
> involving a substance with significant toxicity. This is historical documentation
> faithful to classical hakim sources. Classical preparation (islah/shodhana) and
> dosage must be strictly followed. This catalog entry is not a modern prescription.
```

---

## Template 5: Barbarous Latin Warning Block

Insert when a Latin (Venice 1595/1608) term or passage has been discarded in favour
of the Arabic original.

```markdown
> ⚠️ **CAUTION — BARBAROUS LATIN**: The Venice edition (1595/1608) renders this term
> or passage in a form that is unintelligible, corrupted, or does not faithfully reflect
> the Arabic original *[insert Arabic term here]*. The Bulaq/Cairo Arabic text and, where
> applicable, the Bakhtiar annotated English translation have been used as the authoritative
> basis for this entry. The Latin reading has been preserved in brackets for historical
> reference only: *[Latin form]*.
```

---

## Template 6: Source Attribution Inline Note

Use within a Notes column cell when citing a specific edition.

```markdown
Source: Arabic (Bulaq ed.) Bk. II, Ch. [N] | Cross-checked: Bakhtiar trans. p. [N]
```

Or when Latin was consulted and found reliable:

```markdown
Source: Arabic (Bulaq ed.) | Latin (Venice 1595) consistent — used for historical context only.
```
