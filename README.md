# Monoid

I couldn't find a notetaking tool that fit how I think—CLI-first, plaintext as truth, AI as an optional assistant rather than the driver. So I built my own.

## Philosophy

**CLI-first, human-first, AI-augmented.** Notes are markdown files. AI never overwrites your stuff. Everything is transparent and reversible.

Every note you create is automatically analyzed and tagged with relevant labels. No manual categorization needed—the system figures out what your note is about and applies appropriate tags.
It searches your existing notes by tags and content to pull in relevant context, then synthesizes connections you might have missed. The more notes you have, the smarter it gets.

## How I use it? 

Mainly while grinding leetcode and jotting down problem notes:

```bash
monoid new "Two Sum - use hashmap to store complement, O(n) time"
monoid new "3Sum - sort first, then two pointers from both ends"
monoid new "Maximum Subarray - Kadane's algorithm, track running max"
```

Monoid auto-tags these with labels like `two-pointers`, `sliding-window`, `dp`, `greedy`, `hashmap`, etc.

Later, when you run:

```bash
monoid enhance <note-id>
```

It doesn't just polish that one note. It searches across all your tagged notes, finds patterns (e.g., "these 5 problems all use the two-pointer technique after sorting"), and builds connections you wouldn't have noticed yourself. Over time, your notes become a interconnected knowledge base that surfaces insights across problems.

**The best part: it improves as you use it.** More notes = better context = smarter enhancements.

## Filler Prompts

You can embed AI instructions directly in your notes using `{{{ }}}` syntax. When you run `enhance`, these placeholders get replaced with generated content.

```markdown
# Binary Tree Notes

Here's my array: [1, 2, 3, 4, 5, 6, 7]

{{{ recursive tree of this array }}}
```

After running `monoid enhance <id>`:

```markdown
# Binary Tree Notes

Here's my array: [1, 2, 3, 4, 5, 6, 7]

        1
       / \
      2   3
     / \ / \
    4  5 6  7
```

This is useful for generating diagrams, code snippets, explanations, or any content you want AI to fill in while keeping your notes structured.

## Install

```bash
git clone https://github.com/zhreyu/monoid.git
cd monoid
uv sync  # or pip install -e .
```

## Commands

```bash
monoid new                         # capture (auto-tagged)
monoid list                        # see all notes
monoid show <id>                   # read a note
monoid edit <id>                   # edit in your editor (default: nano)
monoid search "query"              # find by content or tags
monoid enhance <id>                # AI-enhance with cross-note context and implemnets filler prompts 
monoid ask "question"              # Q&A grounded in your notes
monoid graph web                   # visualize connections
```

## Config

```bash
export MONOID_NOTES_DIR="~/monoid-notes"  # where notes live
export OPENAI_API_KEY="sk-..."            # for AI features
export EDITOR="vim"                       # your preferred editor (default: nano)
```

---

MIT License
