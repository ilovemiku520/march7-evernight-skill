# March 7th / Evernight Skill

[中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

A noncommercial fan-roleplay character dialogue Skill based on Honkai: Star Rail. It includes persona and expression rules, external fixed-memory summaries, a source index, and an optional AstrBot + NapCat QQ adapter. Rights to the characters and the original work belong to their respective rights holders; this project is not an official miHoYo product.

## Using the Skill

Copy the `skills/march7-evernight` folder into the skill directory used by a tool that supports `SKILL.md`, or have the tool install that path from this repository. Use `$march7-evernight` to request character dialogue or maintain materials. Read the corresponding reference documents for the current language; `SKILL.en.md`, `SKILL.ja.md`, and `SKILL.ko.md` are translations of the same entry point and may replace the local `SKILL.md`. Do not install language copies under the same name at the same time.

March 7th is the primary persona and is active by default from 07:00 to 21:00 Beijing time; Evernight is active from 21:00 to 07:00 the next day. This is a project roleplay rule, not official canon. March 7th only occasionally imitates Evernight briefly. The two love each other deeply; a real user does not automatically become a spouse, the Trailblazer, or either character.

In replies, first understand the question's intent and the facts, then refer to on-topic verified dialogue wording, and only then improvise a little. Learn the overall word choice, syntax, pauses, transitions, and relationship to the addressee; do not use a mechanical word-substitution table. Evernight's ordinary replies end with a single `♭`; exceptions include strict formats, verbatim quotations, and breaking character.

## External Memory

The public package provides 45 original summaries and an index of 1,000 source records without body text; the latter is deduplicated by character and body hash to 932 entries. The index is not the full dialogue text, nor is it a complete collection of the entire game. Unverified candidates, private chats, machine runtime information, full dialogue transcripts, and original-work images and audio are not included in the public package.

When original lines are needed, verify them against the sources and import them only into local materials you have the right to use. Character expression, source-material lookup, and chat memory are handled separately; fixed materials are not automatically rewritten from user chatter. See the [External Memory Policy](skills/march7-evernight/references/en/memory-policy.md) for details.

## QQ Deployment and Permissions

The Skill itself does not connect to QQ or execute programs. The optional adapter requires the deployer to install AstrBot and NapCat themselves, enter their own model key, and set up their own real administrator account. The public version does not come with anyone's account or credentials preconfigured.

`owner_qq` is empty by default, and computer operations are disabled by default. After setting a framework administrator and filling in `owner_qq`, that real account has persona-management permission by default on every message, with no activation passphrase required. Only if `enable_computer_operations` is separately enabled may a private chat from that account use file and program functions. A web administrator cannot impersonate that QQ identity.

Enabling computer operations allows file reading, writing, appending, directory listing, and PowerShell execution within the permissions of the current Windows account; the default working directory is not a sandbox, and an explicit absolute path may point to another directory. It cannot bypass operating-system permissions or automatically elevate via UAC. Read the [Deployment and Permissions guide](docs/en/deployment.md) before configuring.

## Licensing

The project's original code, rules, and summaries are governed by the [noncommercial license](LICENSE); the English text of the license is authoritative. It permits personal noncommercial use, modification, and noncommercial redistribution with attribution, and prohibits selling, paid bots, paid APIs, advertising monetization, and other commercial uses. Third-party software and original-work assets retain their existing licenses and rights; this license does not grant new rights for them. The source provided here is noncommercial source code and cannot be described as an OSI open-source license.

[Persona Rules](skills/march7-evernight/references/en/persona-rules.md) · [Third-Party Rights Notice](THIRD_PARTY.md) · [Validation Record](qq-adapter/VALIDATION.md)
