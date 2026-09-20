# B0.01 - Locate and read a report

## Outcomes

Find your current directory, identify the file a relative path names, and read
a filename containing a space without accidentally supplying two filenames.

## Understand first

A terminal accepts text and displays results. The **shell** is the program
interpreting the commands you type. A command usually names a program followed
by arguments: information that tells that program what to do. Press Enter to
run one command. Our code blocks omit the shell prompt; type only the commands.

A **file** holds data; a **directory** groups names. The shell has a current
working directory. A relative path is interpreted from there. `..` means the
parent directory. An absolute path begins with `/` and does not depend on the
working directory. Spaces normally separate arguments, so quote a path that
contains a space. Quotes group the argument; they are not part of its name.

The scenario is ordinary on purpose: a delivery team has two reports. Before
we restrict a reader, we need to know which report we actually asked it to read.

## Before you begin

In the VM, return to your repository root. Then:

```bash
./lab-start b0.01
cd .student/b0.01
```

Line by line: `./lab-start` runs the course helper in the current directory and
creates a working copy plus synthetic reports. `cd` changes the shell's working
directory to that copy. Starting again resumes it; it does not erase your work.

The reports already exist: you do not need to create them or type their contents.
`report.txt` and `weekend report.txt` are data to inspect; `README.md` is this
guide. The directory `notes` contains a third text file. A leading `./` means
"in this directory"; `.student` is the course's student-work directory, not a
command. Its leading dot makes it normally hidden in a plain directory listing.

## Exercise 1 - Establish where you are

```bash
pwd
ls
cat report.txt
cat "weekend report.txt"
```

Line by line: `pwd` prints the current directory; its ending should be
`.student/b0.01`. `ls` lists names there. The first `cat` displays the daily
report. The second supplies one quoted filename to display the weekend report.
Expect a generated delivery identifier and parcel counts. Identifiers differ
between attempts; do not compare them against a screenshot or memorize them.

`cat` returns you to the shell after displaying the file. It does not start an
editor, so there is nothing to save or quit. Reading a file is different from
executing instructions in it. Here, parcel-count sentences are just text.
For the daily report, expect this shape (do not type this output):

```text
Delivery report for <generated identifier>
Three parcels arrived.
```

The angle-bracketed phrase represents a changing identifier, not literal file
content. The first line identifies this attempt; the second is the report data.

## Exercise 2 - Make and diagnose a path mistake

Predict which of these commands will fail before running them:

```bash
cd notes
cat location.txt
cat report.txt
cat ../report.txt
cd ..
```

Line by line: `cd notes` enters the child directory. `cat location.txt` reads its
orientation note. `cat report.txt` fails because that name is not in `notes`.
`cat ../report.txt` repairs the lookup by naming the parent's report. `cd ..`
returns to the lesson directory. The missing-file error does **not** show an
access-control denial: we simply asked for the wrong path.

The complete supplied note is:

```text
You are reading a file inside the notes directory.
The delivery reports are one directory above this one.
```

The first line describes location; the second tells you how the reports relate
to it. Neither line changes the filesystem: this is data, not a command.

## Checkpoint - Try without the command sequence

From the lesson directory, enter `notes`, read the weekend report without
leaving `notes`, and return. Explain why the quotes and `..` solve different
problems. If stuck, revisit Exercise 2 and then try again without looking.

Do not proceed until you can predict the result from your current directory.
There is no automatic grade for guided lessons.

## Troubleshooting and finish

If `./lab-start` is missing, you are not at the repository root. If `cd notes`
fails, check `pwd` and `ls`; do not create a replacement directory to hide the
mistake. Use `cd ..` only when you know which parent you intend to enter.

```bash
cd ../..
```

From the lesson directory this returns to the repository root. You may stop
here and resume later. To discard this lesson's files, run from that root:

```bash
./lab-reset b0.01 --dry-run
./lab-reset b0.01 --yes
```

The first command previews removal. The second removes this lesson's workspace
and fixtures, including your edits. It leaves other lessons alone. Reset is
optional, not a prerequisite for starting the next lesson.

## Sources and scope

- [Ubuntu 24.04 Bash manual](https://manpages.ubuntu.com/manpages/noble/man1/bash.1.html),
  QUOTING and SHELL BUILTIN COMMANDS (`cd`, `pwd`): command interpretation and
  navigation. The lab uses ordinary paths without symlink-navigation edge cases.
- [GNU ls manual shipped by Ubuntu](https://manpages.ubuntu.com/manpages/noble/man1/ls.1.html)
  and [GNU cat manual](https://manpages.ubuntu.com/manpages/noble/man1/cat.1.html):
  listing names and displaying file contents.

Report names and parcel counts are North Echo fixtures, not Linux guarantees.
The relative-path failure is an observed exercise result, not evidence of a
security restriction. References support the explanation; opening them is optional.
