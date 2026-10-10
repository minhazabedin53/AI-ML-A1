# DPS970 – Activity 1

Question 1: a simple-reflex **spam filter agent** for `.eml` email files.
Question 2: the **three-jug problem** (12, 8 and 3 gallons → measure 1 gallon) solved with
**breadth-first search** as in AIMA 4e Figure 3.9.

Written answers for 1(a)–(c) and 2(a)–(c), plus implementation notes for 1(d) and 2(d),
are in **`Minhaz Abedin - Activity 1.pdf`**

## Requirements

* Python **3.10 or newer**.
* Nothing to install: the code and tests use only the Python standard library (`unittest`).
* On Windows use `python`; on macOS/Linux you may need `python3` instead.

## Running the tests

From this folder, run everything with one command:

```bash
python run_tests.py
```

Or run each question's suite on its own:

```bash
cd q1_spam_filter
python -m unittest discover -v      # 43 tests

cd ../q2_water_jugs
python -m unittest discover -v      # 22 tests
```

## Running the programs

**Question 1 – sort an inbox:**

```bash
cd q1_spam_filter
python -m spam_filter --inbox test_data/inbox --out output --copy
```

This puts each email into `output/email/` or `output/spam/` and prints which rule decided
each one. Drop `--copy` to *move* the files instead (the behaviour the activity asks for).
Use `--config <folder>` to point at different list files.

**Question 2 – solve the jug puzzle:**

```bash
cd q2_water_jugs
python -m water_jugs                              # 12/8/3 jugs, measure 1 gallon
python -m water_jugs --capacities 5 3 --goal 4    # any other jug puzzle
```

Expected output for the activity's puzzle:

```
Step  Action                                      State
   0  (start)                                     (0, 0, 0)
   1  Fill the 12-gal jug from the faucet         (12, 0, 0)
   2  Pour the 12-gal jug into the 8-gal jug      (4, 8, 0)
   3  Pour the 12-gal jug into the 3-gal jug      (1, 8, 3)

Solved in 3 actions (BFS => fewest possible).
```

## Project layout

```
DPS970_Activity1/
├── README.md                      this file
├── Minhaz Abedin - Activity 1.pdf answers to the written parts
├── run_tests.py                   runs every test
├── .github/workflows/tests.yml    GitHub Actions CI
│
├── q1_spam_filter/
│   ├── spam_filter/
│   │   ├── agents.py              Agent, Environment, Rule, rule_match,
│   │   │                          SimpleReflexAgentProgram (AIMA Fig. 2.10)
│   │   ├── email_percept.py       sensor: parses/decodes .eml files
│   │   ├── spam_agent.py          INTERPRET-INPUT, the condition-action rules, the agent
│   │   ├── environment.py         EmailEnvironment (inbox → email/ or spam/)
│   │   └── __main__.py            command-line program
│   ├── config/                    allow_list.txt, restrict_list.txt, bad_words.txt
│   ├── test_data/
│   │   ├── inbox/                 19 test emails (.eml)
│   │   └── expected_labels.csv    correct folder for each test email, and why
│   └── tests/                     unit tests
│
└── q2_water_jugs/
    ├── water_jugs/
    │   ├── search.py              Problem, Node, expand (Fig. 3.7),
    │   │                          breadth_first_search (Fig. 3.9)
    │   ├── jugs_problem.py        WaterJugsProblem: states, actions, transition model
    │   └── __main__.py            command-line program
    ├── test_data/jug_cases.json   11 puzzles with their expected solution lengths
    └── tests/                     unit tests
```

## Test data

**Question 1** (`q1_spam_filter/test_data/inbox`). Each email checks one behaviour:

| Email | Expected | What it checks |
|---|---|---|
| 01 | email | allow-listed sender beats 10 bad words |
| 02 | spam | restrict-listed sender with a clean body |
| 03 | spam | 9 bad words |
| 04 | email | exactly 5 bad words is **not** more than 5 |
| 05 | spam | 6 bad words |
| 06 | email | clean mail from an unknown sender |
| 07 | spam | bad words hidden in a base64-encoded body |
| 08 | spam | quoted-printable body |
| 09 | spam | HTML-only body (tags and CSS ignored) |
| 10 | spam | bad words in a text attachment |
| 11 | email | bad words inside a PDF attachment are not readable |
| 12 | email | sub-domain of an allow-listed domain |
| 13 | spam | sub-domain of a restrict-listed domain |
| 14 | spam | display name pretends to be an allowed domain |
| 15 | spam | upper case and repeated words count |
| 16 | email | missing `From` header |
| 17 | email | bad words only in the Subject header |
| 18 | email | plain + HTML copies of the same text counted once |
| 19 | email | `freedom`, `cashier`, … are not bad words (whole words only) |

**Question 2** (`q2_water_jugs/test_data/jug_cases.json`): the activity's puzzle plus other
capacities and goals, a custom start state, a goal already true at the start, and two
unsolvable puzzles (BFS must return `failure`).

## Design notes

* Both implementations follow the textbook's pseudocode and the structure of the aima-python
  reference code (`agents.py`, `search4e`): same class and function names, same algorithm steps.
* Spam rule order: allow list → restrict list → more than 5 bad words → default (not spam).
  All assumptions are listed in `WRITTEN_ANSWERS` 1(d).
