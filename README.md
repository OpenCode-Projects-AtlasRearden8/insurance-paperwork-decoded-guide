# Insurance Paperwork, Decoded

An **education-only** manual for reading everyday insurance policies — auto,
renters, homeowners, health, and life — translated section by section into
plain English. Built by [Asdale Dynamics, LLC](https://dylanasdale.github.io)
in the same "explain it like a friend would" spirit as *The Massive AI Manual*.

> **This is never coverage or legal advice.** It teaches you how to *read* your
> own policy and organize your own paperwork. For decisions about what to buy
> or what a denial really means, talk to your state insurance department, a
> licensed agent or broker, or an attorney.

## What's inside

| Path | What it covers |
| --- | --- |
| `docs/00-start-here.md` | How to use this manual, the calm-voice promise |
| `docs/01-how-to-read-a-policy.md` | Anatomy of any policy, section by section |
| `docs/02-money-math.md` | Premiums vs. deductibles vs. out-of-pocket, in plain arithmetic |
| `docs/03-declaration-pages.md` | Decoding the declarations page line by line |
| `docs/04-auto.md` | Auto policies translated |
| `docs/05-renters.md` | Renters policies translated |
| `docs/06-homeowners.md` | Homeowners policies translated |
| `docs/07-health.md` | Health policies translated (see note below) |
| `docs/08-life.md` | Life policies translated |
| `docs/09-claim-filing-walkthrough.md` | Claim walkthroughs + document checklists |
| `docs/10-denial-letters.md` | First responses to a denial letter |
| `docs/11-annual-review-ritual.md` | A once-a-year paperwork ritual |
| `docs/12-glossary.md` | Plain-English glossary |
| `docs/worksheets/` | Policy-binder worksheets you can print or copy |
| `site/` | Generated static HTML (run `python3 build.py`) |

**Health note:** this guide covers health-insurance paperwork in general. For
Medicare-specific reading, see the companion project
*medicare-decoded-guide*.

## How to run it

Local-first: no network, no dependencies beyond Python 3.8+.

```bash
python3 build.py        # builds the static site into site/
python3 -m unittest discover -s tests -v   # runs the test suite
```

Then open `site/index.html` in any browser, or read the markdown directly.

## Design principles

- **Education only.** Every page repeats the disclaimer. Nothing here tells
  you what to buy or files anything for you.
- **Plain arithmetic.** Every money example uses round numbers you can check
  by hand.
- **Calm voice.** Paperwork is stressful. Short sentences, no scolding, no
  urgency theater.
- **Low-energy friendly.** Checklists are broken into small steps so a bad
  day only costs you one step.
- **Local-first.** Your filled-in worksheets stay on your machine.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.
