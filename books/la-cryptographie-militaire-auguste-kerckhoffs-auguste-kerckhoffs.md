---
book: "La Cryptographie militaire — Auguste Kerckhoffs"
genre: "Nonfiction"
bookline: "Military cryptography — the 1883 paper that founded modern cryptanalysis: six desiderata for ciphers, the repeated-fragment key-length attack, and the maxim that a cipher must baffle even its inventor."
---

--- card
id: 918
title: "The enemy knows the system"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["notice what others miss"]
source_locator: "Part 1, §II Desiderata, no. 2"
ripped_at: "2026-10-01"
---
## Steal

Il faut qu'il n'exige pas le secret, et qu'il puisse sans inconvénient tomber entre les mains de l'ennemi. The system must not require secrecy, and must be able to fall into the enemy's hands without inconvenience.

## Why it matters

Security that depends on the method staying hidden dies the day it is captured, reverse-engineered, or leaked. Design as if the enemy already has the blueprint — because eventually they will.

## Use when

When you are evaluating any security system, protocol, or anyone's secret sauce.

--- card
id: 919
title: "A break doesn't expire"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["notice what others miss"]
source_locator: "Part 1, §II (rebuttal of temporary secrecy)"
ripped_at: "2026-10-01"
---
## Steal

Une fois qu'un cryptogramme intercepté a pu être déchiffré, toute nouvelle dépêche, écrite avec la même clef et qui subit le même sort, peut être lue instantanément. Once one intercepted cryptogram is broken, every later dispatch written with the same key can be read instantly.

## Why it matters

Against the claim that war messages only need three or four hours of secrecy: a break compounds. It doesn't expire with the message — it retroactively opens everything ever sent under that key.

## Use when

When you are tempted to reuse a key, password, or credential because this one use is low-stakes.

--- card
id: 920
title: "Secrecy doesn't scale"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["a better question"]
source_locator: "Part 1, §II (the secrecy objection)"
ripped_at: "2026-10-01"
---
## Steal

J'entends par secret, non la clef proprement dite, mais ce qui constitue la partie matérielle du système : tableaux, dictionnaires ou appareils mécaniques. By secrecy I mean not the key itself, but the material part of the system: tables, dictionaries, mechanical devices.

## Why it matters

If the machinery must stay secret, every new user is a new capture risk — so the system can never be issued beyond a handful of generals. A secret you can't distribute is a system you can't deploy.

## Use when

When deciding what in your operation must stay secret versus what must survive exposure.

--- card
id: 921
title: "Destroy the weapon by publishing it"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["make an idea concrete"]
source_locator: "Part 1, §I-B (the Contr'espion precedent, 1793)"
ripped_at: "2026-10-01"
---
## Steal

Ce n'était pas un des moindres services à rendre à la patrie que d'anéantir par la publicité l'arme la plus dangereuse des ennemis secrets. In 1793 Dlandol published the royalists' cipher keys — annihilating by publicity the most dangerous weapon of the Republic's secret enemies.

## Why it matters

Publicity as an offensive move. A broken secret, widely known to be broken, stops being a weapon — nobody will trust a cipher the newspapers have already printed the key to.

## Use when

When you need to kill a bad standard, a compromised credential, or a practice that survives on obscurity.

--- card
id: 922
title: "Every break is two jobs"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["a better question"]
source_locator: "Part 1, §III-B, 2° (two operations of cryptanalysis)"
ripped_at: "2026-10-01"
---
## Steal

Le déchiffrement d'un cryptogramme dont on n'a pas la clef comporte deux opérations bien distinctes : un calcul de probabilité et un travail de tâtonnement. Breaking a cryptogram without the key is two distinct jobs: a probability calculation and groping trial-and-error.

## Why it matters

For polyalphabetic systems the two unknowns are the number of alphabets and their arrangement. Decomposing the attacker's job into countable subproblems is also how the defender prices each layer of defense.

## Use when

When sizing up any adversarial problem — split it into the math and the groping.

--- card
id: 923
title: "Repetition is the leak"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["notice what others miss"]
source_locator: "Part 2, §4°a (the two principles; key-length recovery)"
ripped_at: "2026-10-01"
---
## Steal

Dans tout texte chiffré, deux polygrammes semblables sont le produit de deux groupes de lettres semblables, cryptographiés avec les mêmes alphabets ; le nombre de chiffres compris dans l'intervalle des deux polygrammes est un multiple du nombre des lettres de la clef. Two identical ciphertext fragments come from two identical plaintext groups under the same alphabets — and the distance between them is a multiple of the key length.

## Why it matters

Take the greatest common divisor of the intervals between repeats and you have the key length. Redundancy betrays structure: the key is hiding in the gaps between repeats.

## Use when

When hunting hidden periodicity in any data — ciphertext, logs, signals.

--- card
id: 924
title: "The whole cipher is one letter: E"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["notice what others miss"]
source_locator: "Part 1, §III-B, 2° (the value of a cipher)"
ripped_at: "2026-10-01"
---
## Steal

La valeur d'un chiffre se mesure aux garanties qu'il offre contre la découverte du signe correspondant à cette lettre. The value of a cipher is measured by the guarantees it offers against discovery of the sign for the letter E.

## Why it matters

In French, E is one letter in five. Find the most frequent symbol and the rest of the system unravels by trial. Every substitution-like structure has a load-bearing letter — the defense lives or dies on hiding it.

## Use when

When attacking any substitution-like structure — find the anchor first.

--- card
id: 925
title: "The traitor words"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["notice what others miss"]
source_locator: "Part 2, §4°b (crib-dragging the Havas dispatch)"
ripped_at: "2026-10-01"
---
## Steal

Dans les cas un peu difficiles ce sont généralement les deux ou trois premiers mots qui viennent jouer le rôle de traîtres. In the hard cases it is generally the first two or three words that play the traitors.

## Why it matters

Military dispatches open predictably — le général, vous, ne — so the breaker keeps a classified list of likely openings indexed by where E falls. Every message has a predictable edge; the attacker catalogs it like factory-default passwords.

## Use when

When guessing the predictable parts of any structured message or protocol.

--- card
id: 926
title: "Symmetry of position"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["notice what others miss"]
source_locator: "Part 2, §4°c (symétrie de position)"
ripped_at: "2026-10-01"
---
## Steal

Du moment que les alphabets sont disposés en nombre carré, et que la signification d'un chiffre commun a été trouvée dans deux ou plusieurs alphabets, on peut, au moyen d'une simple addition, déterminer la place que doit occuper dans ces différents alphabets tout nouveau chiffre. In square-arranged alphabets the letters keep their relative order — solve one letter in two alphabets and every other letter transfers by offset.

## Why it matters

Structure leaks sideways. One solved position determines all parallel positions by simple addition — Kerckhoffs notes no cryptography book had ever pointed this out. Regularity is a side channel.

## Use when

When exploiting any regular arrangement — one solved cell positions the whole grid.

--- card
id: 927
title: "One key per message"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["a better question"]
source_locator: "Part 2, §4°d (the stacked-cryptograms attack)"
ripped_at: "2026-10-01"
---
## Steal

Quelle que soit la disposition adoptée des alphabets, les correspondants sont toujours tenus d'écrire chacune de leurs dépêches avec une clef différente. Whatever the alphabets, correspondents must write each dispatch with a different key.

## Why it matters

Stack a dozen short cryptograms under one key, align them in columns, and the frequency math works across all of them at once. Reusing a key pools many small unbreakable texts into one big breakable one.

## Use when

When reusing any secret across sessions — each reuse feeds the same attack.

--- card
id: 928
title: "Ars ipsi secreta magistro"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "passage"
intents: ["a better question"]
source_locator: "Part 2, §IV (closing maxim, after Du Carlet 1644)"
ripped_at: "2026-10-01"
---
## Steal

Un chiffre n'est bon qu'autant qu'il reste indéchiffrable pour le maître lui-même qui l'a inventé : Ars ipsi secreta magistro. A cipher is only good insofar as it remains indecipherable to the very master who invented it.

## Why it matters

Borrowed from Du Carlet (1644) as the closing line of the whole paper. The ultimate test isn't whether strangers fail to break your system — it's whether you, holding every advantage, cannot read it either.

## Use when

When testing your own system, argument, or lock — try to break it with the home-field advantage.

--- card
id: 929
title: "Teach your officers to break it"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["make an idea concrete"]
source_locator: "Part 1, §II (the open-teaching demand)"
ripped_at: "2026-10-01"
---
## Steal

Ce ne sera que lorsque nos officiers auront étudié les principes de la cryptographie et appris l'art de déchiffrer, qu'ils seront en état d'éviter les nombreuses bévues qui compromettent la clef des meilleurs chiffres. Only when our officers have studied cryptography and learned the art of breaking will they avoid the blunders that compromise the key of the best ciphers.

## Why it matters

The Germans drilled every officer in cryptanalysis; the French issued ciphers nobody understood. Users who can't attack the system will misuse it into insecurity — the weakest link is the operator, so train the operator as an attacker.

## Use when

When rolling out any security practice to non-experts — teach the break first.

--- card
id: 930
title: "Beaufort unmasked"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["notice what others miss"]
source_locator: "Part 1, §III-B, 3°d (système de Beaufort)"
ripped_at: "2026-10-01"
---
## Steal

Tous ces appareils ne sont en réalité autre chose qu'un simple tableau de Vigenère. The English marveled at Admiral Beaufort's supposedly indecipherable system — it is Vigenère with a reversed alphabet, nothing more.

## Why it matters

Most celebrated new systems are old systems in costume. Before awe, check for isomorphism: relabel the parts and see if the machine you already know is hiding inside.

## Use when

When someone pitches you a revolutionary method — strip the costume first.

--- card
id: 931
title: "Krohn's 3,200 alphabets"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "concept"
intents: ["a better question"]
source_locator: "Part 2, §4°b, footnote (Krohn, 1873)"
ripped_at: "2026-10-01"
---
## Steal

Ce n'est pas la possibilité de se servir d'un grand nombre d'alphabets différents qui donne de la valeur à un système, mais plutôt la difficulté plus ou moins grande de déterminer le nombre des alphabets employés. Krohn built a dictionary of 3,200 alphabets — c'est à la fois trop et trop peu: too much and too little.

## Why it matters

What matters isn't how many alphabets you have, it's how hard it is to determine how many you used. Complexity theater: the metric being maximized is not the metric that matters.

## Use when

When someone dazzles you with big numbers — ask which number the attacker actually needs.

--- card
id: 932
title: "One wrong digit, wrong war"
field_order: ["title", "book", "type", "steal", "why", "uw", "id", "intents", "source_locator", "ripped_at"]
type: "mechanism"
intents: ["make an idea concrete"]
source_locator: "Part 2, §C (dictionnaires chiffrés; the Andrassy cable)"
ripped_at: "2026-10-01"
---
## Steal

Qu'un seul chiffre dans un groupe soit fautif, que le télégraphe mette un 3 où il faut un 5, et le sens sera complètement changé. One wrong digit in a code group and the meaning is completely changed — an Italian cable once turned an embassy attaché into Count Andrassy.

## Why it matters

Codebooks fail silently and totally: a garbled group doesn't look garbled, it looks like a different order. In 1870 half the army's dispatches arrived partly illegible. A system whose failure mode is confident misreading will misread confidently.

## Use when

When designing anything where a typo changes the order — make errors loud, not plausible.
