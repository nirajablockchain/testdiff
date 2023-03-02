#!/usr/bin/env python3

import asyncio
import openai
import os
import subprocess
import sys

DIFF_PROMPT = "Generate a succinct summary of the following code changes:"
COMMIT_MSG_PROMPT = "Using no more than 50 characters, generate a descriptive commit message from these summaries:"
PROMPT_CUTOFF = 10000
###openai.organization = os.getenv("OPENAI_ORG_ID")
openai.api_key = ""


def get_diff():
    arguments = [
        "git", "--no-pager", "diff", "--staged", "--ignore-space-change",
        "--ignore-all-space", "--ignore-blank-lines" ,"main.py"
    ]
    diff_process = subprocess.run(arguments, capture_output=True, text=True)
    diff_process.check_returncode()
    return diff_process.stdout.strip()


def parse_diff(diff):
    file_diffs = diff.split("\ndiff")
    file_diffs = [file_diffs[0]
                  ] + ["\ndiff" + file_diff for file_diff in file_diffs[1:]]
    chunked_file_diffs = []
    for file_diff in file_diffs:
        [head, *chunks] = file_diff.split("\n@@")
        chunks = ["\n@@" + chunk for chunk in reversed(chunks)]
        chunked_file_diffs.append((head, chunks))
    return chunked_file_diffs


def assemble_diffs(parsed_diffs, cutoff):
    # create multiple well-formatted diff strings, each being shorter than cutoff
    assembled_diffs = [""]

    def add_chunk(chunk):
        if len(assembled_diffs[-1]) + len(chunk) <= cutoff:
            assembled_diffs[-1] += "\n" + chunk
            return True
        else:
            assembled_diffs.append(chunk)
            return False

    for head, chunks in parsed_diffs:
        if not chunks:
            add_chunk(head)
        else:
            add_chunk(head + chunks.pop())
        while chunks:
            if not add_chunk(chunks.pop()):
                assembled_diffs[-1] = head + assembled_diffs[-1]
    return assembled_diffs


async def complete(prompt):
    print(prompt[:PROMPT_CUTOFF + 100])
    completion_resp = openai.Completion.create(
        model="code-davinci-002",
        prompt=prompt[:PROMPT_CUTOFF + 100],
        temperature=0,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\"\"\""]
    )
    # completion_resp = await openai.ChatCompletion.acreate(
    #     model="code-davinci-002",
    #     messages=[{
    #         "role": "user",
    #         "content": prompt[:PROMPT_CUTOFF + 100]
    #     }],
    #     max_tokens=128)
    #completion = completion_resp.choices[0].message.content.strip()
    print(completion_resp)
    return completion_resp


async def summarize_diff(diff):
    assert diff
    return await complete(DIFF_PROMPT + "\n\n" + diff + "\n\n")


async def summarize_summaries(summaries):
    assert summaries
    return await complete(COMMIT_MSG_PROMPT + "\n\n" + summaries + "\n\n")


async def generate_commit_message(diff):
    if not diff:
        # no files staged or only whitespace diffs
        return "Fix whitespace"

    assembled_diffs = assemble_diffs(parse_diff(diff), PROMPT_CUTOFF)
    summaries = await asyncio.gather(
        *[summarize_diff(diff) for diff in assembled_diffs])
    return await summarize_summaries("\n".join(summaries))


def commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message,
                           "--edit"]).returncode


async def main():
    try:
        diff = get_diff()
        commit_message = await generate_commit_message(diff)
    except UnicodeDecodeError:
        print("gpt-commit does not support binary files", file=sys.stderr)
        commit_message = "# gpt-commit does not support binary files. Please enter a commit message manually or unstage any binary files."

    if "--print-message" in sys.argv:
        print(commit_message)
    else:
        exit(commit(commit_message))


if __name__ == "__main__":
    asyncio.run(main())