import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const SYSTEM_PROMPT = `You are enhancing a personal note. Your job:

1. PROSE IMPROVEMENT: Tighten the English, fix grammar, improve clarity. Keep the original tone and voice. Don't make it formal unless it was already formal. Keep the casual vibe if it's casual.

2. CONTENT AUGMENTATION: If you notice misconceptions, incomplete reasoning, or opportunities to add valuable context, weave corrections/additions naturally into the text. For DSA notes, point out edge cases, alternative approaches, or complexity considerations. Don't be preachy - just add value where it matters.

3. COMMAND EXPANSION: Find all {{{...}}} blocks. These are natural language commands. Expand each into actual content:
   - Tree diagrams → ASCII art showing the structure
   - State space exploration → Show the decision tree with final answers (don't need to show all intermediate states, focus on the key decisions and outcomes)
   - Complexity analysis → Big-O with brief explanation
   - Example walkthrough → Step-by-step trace
   - Edge cases → Bulleted list
   - Intuition → Clear explanation

   Wrap each expanded section like this:
   ****
   [expanded content here]
   ****

4. CRITICAL OUTPUT RULES:
   - DO NOT use markdown formatting (no #, ##, **, \`, etc.) - output plain text only
   - DO NOT add ANY intro text like "Here's the enhanced note:" or "Here is your enhanced note:"
   - DO NOT add ANY conclusion/summary text at the end like "This enhancement clarifies..." or "I've improved..."
   - DO NOT add meta-commentary about what you changed or fixed
   - JUST output the enhanced note content directly - nothing before, nothing after
   - Start your response with the actual note content, not preamble

5. OTHER CONSTRAINTS:
   - NEVER remove the user's original content - only enhance it
   - Keep the same structure/headings the user had
   - Be concise - don't add fluff
   - For DSA: focus on intuition and patterns, not just code
   - Output the COMPLETE enhanced note, not just the changes`;

function cleanEnhancedOutput(content: string): string {
  const lines = content.trim().split('\n');

  const introPatterns = [
    /^here'?s?\s+(the\s+)?enhanced\s+(note|version)/i,
    /^enhanced\s+note:?\s*$/i,
    /^---+\s*$/,
  ];

  const conclusionPatterns = [
    /^this\s+enhancement\s+(clarifies|improves|provides)/i,
    /^i'?ve?\s+(enhanced|improved|clarified|polished)/i,
    /^the\s+(above\s+)?enhancement\s+/i,
    /^hope\s+this\s+helps/i,
    /^let\s+me\s+know\s+if/i,
  ];

  while (lines.length > 0) {
    const line = lines[0].trim().toLowerCase();
    if (!line) {
      lines.shift();
      continue;
    }
    if (introPatterns.some((p) => p.test(line))) {
      lines.shift();
      continue;
    }
    break;
  }

  while (lines.length > 0) {
    const line = lines[lines.length - 1].trim().toLowerCase();
    if (!line) {
      lines.pop();
      continue;
    }
    if (conclusionPatterns.some((p) => p.test(line))) {
      lines.pop();
      continue;
    }
    break;
  }

  return lines.join('\n').trim();
}

export async function POST(request: NextRequest) {
  try {
    const { content, prompt, context } = await request.json();

    if (!content) {
      return NextResponse.json(
        { error: 'Content is required' },
        { status: 400 }
      );
    }

    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { error: 'OpenAI API key not configured' },
        { status: 500 }
      );
    }

    let userContent = `Enhance this note:\n\n${content}`;

    if (context) {
      userContent = `Related notes for context:\n${context}\n\n---\n\n${userContent}`;
    }

    if (prompt) {
      userContent += `\n\nAdditional instructions: ${prompt}`;
    }

    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userContent },
      ],
    });

    const rawOutput = response.choices[0].message.content || '';
    const enhanced = cleanEnhancedOutput(rawOutput);

    return NextResponse.json({ enhanced });
  } catch (error) {
    console.error('Enhancement error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Enhancement failed' },
      { status: 500 }
    );
  }
}
