#!/usr/bin/env python3

import asyncio
import openai
import os
import subprocess
import sys
import git
PIPE = subprocess.PIPE

DIFF_PROMPT = "Generate a detailed summary of the following code changes in English and if you're unsure of the answer, dont add :"
COMMIT_MSG_PROMPT = "Using no more than 1000 characters, generate a descriptive commit message from these summaries:"
PROMPT_CUTOFF = 1000

openai.api_key = "pppppp"


def get_diff():
    arguments = "git diff --ignore-blank-lines --ignore-all-space --ignore-space-change --diff-filter=CMRTUXB master"
    command = subprocess.Popen(arguments.split(), stdout=PIPE, stderr=PIPE)
    stdoutput, stderroutput = command.communicate()
    return stdoutput.decode('utf-8')


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
    if prompt[:PROMPT_CUTOFF + 100].strip() ==DIFF_PROMPT:
        return ""
    completion_resp = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt[:PROMPT_CUTOFF].strip() +"\"\"\"" ,
        temperature=0,
        max_tokens=3500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\"\"\""]
    )

    #print(completion_resp)
    return completion_resp


async def summarize_diff(diff):
    #assert diff
    return await complete(DIFF_PROMPT + "\n\n" + diff + "\n\n")


async def summarize_summaries(summaries):
    #assert summaries
    return await complete(COMMIT_MSG_PROMPT + "\n\n" + summaries + "\n\n")


async def generate_commit_message(diff):
    if not diff:
        # no files staged or only whitespace diffs
        return "Fix whitespace"

    assembled_diffs = assemble_diffs(parse_diff(diff), PROMPT_CUTOFF)
    summaries = await asyncio.gather(
        *[summarize_diff(diff) for diff in assembled_diffs])
    final_summary = ""
    for summary in summaries :
        if summary != "":
            final_summary = final_summary + summary["choices"][0]["text"].strip() +".\t"
    #return final_summary
    print("\n Final Summary: " + final_summary)
    return await summarize_summaries(final_summary)

#
# def commit(message):
#     # will ignore message if diff is empty
#     return subprocess.run(["git", "commit", "--message", message,
#                            "--edit"]).returncode


async def main():
    try:
        diff = get_diff()
        print ("\n Git Diff : " + diff)
        commit_message = await generate_commit_message(diff)
    except UnicodeDecodeError:
        print("gpt-commit does not support binary files", file=sys.stderr)
        commit_message = "# gpt-commit does not support binary files. Please enter a commit message manually or unstage any binary files."

    # if "--print-message" in sys.argv:
    print("\n Commit Message Summarized : " + commit_message["choices"][0]["text"].strip())
    # else:
    #     #exit(commit(commit_message))


if __name__ == "__main__":
    asyncio.run(main())