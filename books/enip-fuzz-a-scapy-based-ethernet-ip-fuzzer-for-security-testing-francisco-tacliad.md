---
book: "ENIP Fuzz: a Scapy-based EtherNet/IP fuzzer for security testing — Francisco Tacliad"
genre: "Thesis"
bookline: "Masters thesis — Naval Postgraduate School, 2016. Full text: https://archive.org/details/enipfuzzscapybas1094556714"
---

--- card
id: 383
title: "ENIP Fuzz: a Scapy-based EtherNet/IP fuzzer for security testing"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

EtherNet/IP is an industrial control protocol built on TCP/IP — extending TCP/IP to industrial control systems made them "more readily accessible to the outside world," and embedded control systems on Navy afloat and ashore platforms use EtherNet/IP, making those platforms prime targets for cyber attack; the thesis built ENIP Fuzz, a Scapy-based fuzzer, to test a proprietary EtherNet/IP implementation's susceptibility to malformed packets.

## Why it matters

The protocols that run ships, plants, and grids were bolted onto the internet's plumbing — and the way to find their holes before attackers do is to throw malformed packets at them deliberately.

## Use when

Probe your systems the way an attacker would — security lives in the implementation, not the diagram, and fuzzing is how you make the diagram tell the truth.
