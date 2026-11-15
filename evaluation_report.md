# Evaluation Report

Offline guardrail checks: **37/37 passed**.


## Input validation

| Input | Expected behavior | Result |
|---|---|---|
| `[bicycle] 'Does it have wheels?'` | accepted | PASS |
| `[bicycle] 'does it have wheels'` | rejected: no question mark | PASS |
| `[bicycle] '   '` | rejected: empty | PASS |
| `[bicycle] '?'` | rejected: too short | PASS |
| `[bicycle] 'Is it a bike?'` | rejected: names the answer (alias) | PASS |
| `[bicycle] 'Is it a BICYCLE?'` | rejected: names the answer (capitals) | PASS |
| `[bicycle] 'Does it have wheels?'` | rejected: duplicate | PASS |
| `[bicycle] 'Is it big? very very very very very very very v...'` | rejected: too long | PASS |
| `[cat] 'Is it located in a house?'` | accepted: 'located' is not 'cat' | PASS |
| `[cat] 'Is it a kitten?'` | rejected: names the answer (alias) | PASS |

## Response validator

| Input | Expected behavior | Result |
|---|---|---|
| `[bicycle] 'Yes, it has two of them.'` | accepted: starts with a verdict | PASS |
| `[bicycle] 'no'` | accepted: lowercase verdict | PASS |
| `[bicycle] 'Maybe, hard to say.'` | rejected: no Yes/No/Sometimes/Unclear start | PASS |
| `[bicycle] 'Yes, a bicycle has wheels.'` | rejected: reveals the name | PASS |
| `[bicycle] 'Yes, it is a bike.'` | rejected: reveals an alias | PASS |
| `[bicycle] 'Yes, you can cycle on it.'` | rejected: reveals part of the name | PASS |
| `[bicycle] ''` | rejected: empty reply | PASS |
| `[bicycle] None` | rejected: no reply | PASS |
| `[bicycle] 'Yes xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'` | rejected: rambling reply | PASS |
| `[cat] 'Yes, it purrs.'` | accepted | PASS |
| `[cat] 'Yes, like a kitten.'` | rejected: reveals an alias | PASS |

## Guess checker

| Input | Expected behavior | Result |
|---|---|---|
| `[bicycle] 'bicycle'` | expected Win | PASS |
| `[bicycle] 'A BIKE!'` | expected Win | PASS |
| `[bicycle] 'car'` | expected Wrong | PASS |
| `[bicycle] '   '` | expected Invalid | PASS |
| `[bicycle] '!!!'` | expected Invalid | PASS |
| `[cat] 'cats'` | expected Wrong | PASS |
| `[venus flytrap] 'flytrap'` | expected Win | PASS |
| `[sphinx] 'sphynx'` | expected Win | PASS |
| `[sphinx] 'cat'` | expected Wrong | PASS |
| `[gouda] 'cheese'` | expected Wrong | PASS |
| `'CAT!!' after 'cat'` | repeat is detected | PASS |

## Database

| Input | Expected behavior | Result |
|---|---|---|
| `30 objects x their hints` | no hint contains any part of its answer | PASS |
| `hint generator, every object` | never repeats and eventually runs out | PASS |
| `tiers` | 5 Easy, 10 Normal, 15 Hard, 30 unique names | PASS |
| `every name as a guess for every other object` | never wins | PASS |

## Witty replies

| Input | Expected behavior | Result |
|---|---|---|
| `15 lines x 30 objects` | none can hint at any answer | PASS |
